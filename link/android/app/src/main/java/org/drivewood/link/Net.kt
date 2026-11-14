package org.drivewood.link

import android.content.Context
import android.net.wifi.WifiManager
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import org.json.JSONObject
import java.io.DataInputStream
import java.io.DataOutputStream
import java.io.InputStream
import java.io.OutputStream
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.NetworkInterface
import java.net.Socket
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.MessageDigest
import java.security.cert.X509Certificate
import java.security.spec.ECGenParameterSpec
import java.util.concurrent.ConcurrentHashMap
import javax.net.ssl.KeyManagerFactory
import javax.net.ssl.SSLContext
import javax.net.ssl.SSLServerSocket
import javax.net.ssl.SSLSocket
import javax.net.ssl.X509TrustManager
import javax.security.auth.x500.X500Principal

/** Same wire format as the desktop: 4-byte big-endian length + JSON header (+ "size" raw bytes). */
class Wire(sock: Socket) {
    val input = DataInputStream(sock.getInputStream().buffered(1 shl 16))
    private val output = DataOutputStream(sock.getOutputStream().buffered(1 shl 16))
    val rawOut: OutputStream get() = output

    @Synchronized
    fun send(header: JSONObject, payload: ByteArray? = null) {
        if (payload != null && payload.isNotEmpty()) header.put("size", payload.size)
        val raw = header.toString().toByteArray()
        output.writeInt(raw.size); output.write(raw)
        if (payload != null) output.write(payload)
        output.flush()
    }

    fun recv(): JSONObject {
        val n = input.readInt()
        if (n < 0 || n > (1 shl 20)) throw java.io.IOException("bad header")
        val b = ByteArray(n); input.readFully(b)
        return JSONObject(String(b))
    }

    fun recvPayload(h: JSONObject): ByteArray {
        val n = h.optInt("size", 0)
        if (n < 0 || n > (64 shl 20)) throw java.io.IOException("payload too large")
        val b = ByteArray(n); input.readFully(b); return b
    }

    fun flush() = output.flush()
}

/** Device key + self-signed certificate kept in the Android Keystore (the key never leaves it). */
object Identity {
    private const val ALIAS = "drivewood-link-device"

    private fun keyStore() = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    fun ensure() {
        val ks = keyStore()
        if (ks.containsAlias(ALIAS)) return
        val gen = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore")
        gen.initialize(KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY)
            .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
            .setDigests(KeyProperties.DIGEST_SHA256, KeyProperties.DIGEST_SHA384, KeyProperties.DIGEST_NONE)
            .setCertificateSubject(X500Principal("CN=DriveWood Link device"))
            .setCertificateNotAfter(java.util.Date(System.currentTimeMillis() + 3650L * 86400000))
            .build())
        gen.generateKeyPair()
    }

    /** Forget this device's key (a removed device gets a new identity if it signs in again). */
    fun reset() { try { keyStore().deleteEntry(ALIAS) } catch (e: Exception) { } }

    fun fingerprint(): String {
        ensure()
        val cert = keyStore().getCertificate(ALIAS)
        return sha256Hex(cert.encoded)
    }

    fun serverSocket(port: Int): SSLServerSocket {
        ensure()
        val kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm())
        kmf.init(keyStore(), null)
        val ctx = SSLContext.getInstance("TLS")
        ctx.init(kmf.keyManagers, null, null)
        val s = ctx.serverSocketFactory.createServerSocket() as SSLServerSocket
        s.reuseAddress = true
        s.bind(InetSocketAddress(port))
        return s
    }

    /** TLS client that only accepts the server certificate registered in Supabase (pinning). */
    fun connect(host: String, port: Int, expected: String?): SSLSocket {
        val pin = object : X509TrustManager {
            override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) {}
            override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {
                if (expected == null || chain.isEmpty() || sha256Hex(chain[0].encoded) != expected)
                    throw java.security.cert.CertificateException("device identity check failed")
            }
            override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf()
        }
        val ctx = SSLContext.getInstance("TLS")
        ctx.init(null, arrayOf(pin), null)
        val raw = Socket()
        raw.connect(InetSocketAddress(host, port), 8000)
        val s = ctx.socketFactory.createSocket(raw, host, port, true) as SSLSocket
        s.startHandshake()
        return s
    }

    fun sha256Hex(b: ByteArray) = MessageDigest.getInstance("SHA-256").digest(b).joinToString("") { "%02x".format(it) }
}

fun localIp(): String {
    for (ni in NetworkInterface.getNetworkInterfaces()) {
        if (!ni.isUp || ni.isLoopback) continue
        for (a in ni.inetAddresses) if (a is Inet4Address && !a.isLoopbackAddress) return a.hostAddress ?: continue
    }
    return "127.0.0.1"
}

/** LAN announcements (same format as the desktop). Only ids travel here; ownership is checked with Supabase. */
class Discovery(ctx: Context, private val deviceId: String, private val onChange: () -> Unit) {
    val seen = ConcurrentHashMap<String, Triple<String, Int, Long>>()
    @Volatile private var running = true
    private val lock = (ctx.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager)
        .createMulticastLock("dwlink").apply { setReferenceCounted(false) }

    fun start() {
        lock.acquire()
        Thread({ listen() }, "dw-discovery-in").apply { isDaemon = true }.start()
        Thread({ announce() }, "dw-discovery-out").apply { isDaemon = true }.start()
    }

    fun stop() { running = false; if (lock.isHeld) lock.release() }

    private fun announce() {
        val msg = JSONObject().put("app", Config.APP_ID).put("v", Config.PROTOCOL)
            .put("device", deviceId).put("port", Config.TCP_PORT).toString().toByteArray()
        DatagramSocket().use { s ->
            s.broadcast = true
            while (running) {
                try { s.send(DatagramPacket(msg, msg.size, InetAddress.getByName("255.255.255.255"), Config.UDP_PORT)) } catch (e: Exception) { }
                Thread.sleep(3000)
            }
        }
    }

    private fun listen() {
        val s = DatagramSocket(null).apply { reuseAddress = true; bind(InetSocketAddress(Config.UDP_PORT)) }
        val buf = ByteArray(2048)
        while (running) {
            try {
                val p = DatagramPacket(buf, buf.size)
                s.receive(p)
                val m = JSONObject(String(p.data, 0, p.length))
                if (m.optString("app") != Config.APP_ID) continue
                val dev = m.optString("device")
                if (dev == deviceId || dev.isEmpty()) continue
                val addr = p.address.hostAddress ?: continue
                val port = m.optInt("port", Config.TCP_PORT)
                val old = seen[dev]
                seen[dev] = Triple(addr, port, System.currentTimeMillis())
                if (old == null || old.first != addr) onChange()
            } catch (e: Exception) { }
        }
        s.close()
    }

    fun online(id: String) = seen[id]?.let { System.currentTimeMillis() - it.third < 12000 } ?: false
    fun address(id: String) = seen[id]?.let { it.first to it.second }
}

fun InputStream.copyCounted(out: OutputStream, total: Long, onChunk: (Long) -> Unit) {
    val buf = ByteArray(1 shl 16); var left = total; var done = 0L
    while (left > 0) {
        val n = read(buf, 0, minOf(buf.size.toLong(), left).toInt())
        if (n < 0) throw java.io.IOException("transfer interrupted")
        out.write(buf, 0, n); left -= n; done += n; onChunk(done)
    }
}

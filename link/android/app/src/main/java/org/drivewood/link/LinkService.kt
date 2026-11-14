package org.drivewood.link

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.ClipData
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.provider.MediaStore
import android.provider.OpenableColumns
import android.util.DisplayMetrics
import android.view.WindowManager
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.security.MessageDigest
import java.util.concurrent.CompletableFuture
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

/** Runs in the background: receives files/text, answers take-control requests, keeps the device online. */
class LinkService : Service() {
    lateinit var supa: Supa
    var discovery: Discovery? = null
    @Volatile var devices: List<JSONObject> = emptyList()
    private val tokenCache = ConcurrentHashMap<String, Pair<String?, Long>>()
    @Volatile private var running = false
    private val listeners = mutableListOf<() -> Unit>()

    // take control (this phone being controlled)
    @Volatile var pendingDecision: CompletableFuture<Intent?>? = null
    @Volatile var controlStop: (() -> Unit)? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        instance = this
        supa = Supa(this)
        channels()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP_CONTROL) { controlStop?.invoke(); return START_STICKY }
        startForeground(NOTE_ID, statusNote("Ready to receive from your devices"),
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        if (!running && supa.signedIn && deviceId(this) != null) {
            running = true
            discovery = Discovery(this, deviceId(this)!!) { notifyChanged() }.also { it.start() }
            Thread({ serve() }, "dw-server").apply { isDaemon = true }.start()
            Thread({ heartbeatLoop() }, "dw-heartbeat").apply { isDaemon = true }.start()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        running = false
        discovery?.stop()
        instance = null
        super.onDestroy()
    }

    fun addListener(l: () -> Unit) { synchronized(listeners) { listeners.add(l) } }
    fun removeListener(l: () -> Unit) { synchronized(listeners) { listeners.remove(l) } }
    private fun notifyChanged() { synchronized(listeners) { listeners.toList() }.forEach { it() } }

    // --- account data -------------------------------------------------------------
    private fun heartbeatLoop() {
        while (running) {
            try {
                heartbeat(this, supa)
                refreshDevices()
            } catch (e: Exception) { }
            Thread.sleep(60000)
        }
    }

    fun refreshDevices(): List<JSONObject> {
        val arr = supa.rest("GET", "devices?select=id,name,kind,cert_sha256,lan_addr,last_seen&order=name") as JSONArray
        devices = (0 until arr.length()).map { arr.getJSONObject(it) }
        notifyChanged()
        return devices
    }

    fun others() = devices.filter { it.optString("id") != deviceId(this) }
    fun isOnline(d: JSONObject) = discovery?.online(d.optString("id")) ?: false

    private fun log(kind: String, name: String, size: Long, to: String?, from: String?, ok: Boolean) {
        try {
            supa.rest("POST", "transfers", JSONObject().put("kind", kind).put("name", name.take(255)).put("size", size)
                .put("ok", ok).put("to_device", to ?: JSONObject.NULL).put("from_device", from ?: JSONObject.NULL))
        } catch (e: Exception) { }
    }

    // --- server -------------------------------------------------------------------
    private fun serve() {
        val srv = try { Identity.serverSocket(Config.TCP_PORT) } catch (e: Exception) { return }
        while (running) {
            val c = try { srv.accept() } catch (e: Exception) { continue }
            Thread({ handle(c) }, "dw-conn").apply { isDaemon = true }.start()
        }
    }

    private fun ownerOf(token: String): String? {
        tokenCache[token]?.let { if (System.currentTimeMillis() - it.second < 300000) return it.first }
        val uid = Supa.verifyToken(token)
        tokenCache[token] = uid to System.currentTimeMillis()
        return uid
    }

    private fun deviceById(id: String): JSONObject? =
        devices.firstOrNull { it.optString("id") == id } ?: try { refreshDevices().firstOrNull { it.optString("id") == id } } catch (e: Exception) { null }

    private fun handle(sock: java.net.Socket) {
        try {
            sock.soTimeout = 20000
            val w = Wire(sock)
            val hello = w.recv()
            if (hello.optString("t") != "hello") return
            val owner = ownerOf(hello.optString("token"))
            val dev = if (owner != null && owner == supa.userId) deviceById(hello.optString("device")) else null
            if (dev == null) { w.send(JSONObject().put("t", "err").put("msg", "not your device")); return }
            w.send(JSONObject().put("t", "ok").put("name", deviceName(this)))
            val req = w.recv()
            when (req.optString("t")) {
                "text", "clip" -> {
                    w.send(JSONObject().put("t", "done").put("ok", true))
                    val text = req.optString("text")
                    (getSystemService(CLIPBOARD_SERVICE) as ClipboardManager)
                        .setPrimaryClip(ClipData.newPlainText("DriveWood Link", text))
                    if (req.optString("t") == "text")
                        show("Text from ${dev.optString("name")} (copied)", text, 2000 + text.hashCode() % 1000)
                }
                "file" -> receiveFile(sock, w, dev, req)
                "control" -> { sock.soTimeout = 0; beControlled(w, dev) }
            }
        } catch (e: Exception) {
        } finally {
            try { sock.close() } catch (e: Exception) { }
        }
    }

    private fun receiveFile(sock: java.net.Socket, w: Wire, dev: JSONObject, req: JSONObject) {
        val name = req.optString("name", "file").substringAfterLast('/').substringAfterLast('\\')
            .filter { it !in "\\/:*?\"<>|\u0000" }.take(200).ifBlank { "file" }
        val size = req.getLong("size"); val want = req.optString("sha256")
        sock.soTimeout = 60000
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, name)
            put(MediaStore.Downloads.RELATIVE_PATH, "Download/DriveWood Link")
            put(MediaStore.Downloads.IS_PENDING, 1)
        }
        val uri = contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values) ?: return
        val md = MessageDigest.getInstance("SHA-256")
        try {
            contentResolver.openOutputStream(uri)!!.use { out ->
                val hashing = object : java.io.OutputStream() {
                    override fun write(b: Int) { out.write(b); md.update(b.toByte()) }
                    override fun write(b: ByteArray, off: Int, len: Int) { out.write(b, off, len); md.update(b, off, len) }
                }
                w.input.copyCounted(hashing, size) { }
            }
        } catch (e: Exception) { contentResolver.delete(uri, null, null); throw e }
        val ok = md.digest().joinToString("") { "%02x".format(it) } == want
        if (ok) contentResolver.update(uri, ContentValues().apply { put(MediaStore.Downloads.IS_PENDING, 0) }, null, null)
        else contentResolver.delete(uri, null, null)
        w.send(JSONObject().put("t", "done").put("ok", ok))
        if (ok) show("File from ${dev.optString("name")}", "$name is in Downloads/DriveWood Link", 3000)
    }

    // --- outgoing -----------------------------------------------------------------
    private fun open(dev: JSONObject): Pair<java.net.Socket, Wire> {
        val addr = discovery?.address(dev.optString("id"))
            ?: dev.optString("lan_addr").takeIf { it.isNotEmpty() }?.let { it to Config.TCP_PORT }
            ?: throw SupaException("${dev.optString("name")} is not on this network")
        val s = Identity.connect(addr.first, addr.second, dev.optString("cert_sha256").ifEmpty { null })
        val w = Wire(s)
        w.send(JSONObject().put("t", "hello").put("device", deviceId(this)).put("token", supa.token()).put("v", Config.PROTOCOL))
        val r = w.recv()
        if (r.optString("t") != "ok") { s.close(); throw SupaException(r.optString("msg", "refused")) }
        return s to w
    }

    fun sendText(dev: JSONObject, text: String): Boolean {
        val (s, w) = open(dev)
        val ok = s.use { w.send(JSONObject().put("t", "text").put("text", text)); w.recv().optBoolean("ok") }
        log("text", text.take(60), text.toByteArray().size.toLong(), dev.optString("id"), deviceId(this), ok)
        return ok
    }

    fun sendFile(dev: JSONObject, uri: Uri, progress: (Long, Long) -> Unit = { _, _ -> }): Boolean {
        var name = "file"; var size = -1L
        contentResolver.query(uri, null, null, null, null)?.use { c ->
            if (c.moveToFirst()) {
                c.getColumnIndex(OpenableColumns.DISPLAY_NAME).takeIf { it >= 0 }?.let { name = c.getString(it) ?: name }
                c.getColumnIndex(OpenableColumns.SIZE).takeIf { it >= 0 }?.let { if (!c.isNull(it)) size = c.getLong(it) }
            }
        }
        val md = MessageDigest.getInstance("SHA-256"); var counted = 0L
        contentResolver.openInputStream(uri)!!.use { inp ->
            val buf = ByteArray(1 shl 16)
            while (true) { val n = inp.read(buf); if (n < 0) break; md.update(buf, 0, n); counted += n }
        }
        size = counted
        val sum = md.digest().joinToString("") { "%02x".format(it) }
        val (s, w) = open(dev)
        val ok = s.use {
            w.send(JSONObject().put("t", "file").put("name", name).put("size", size).put("sha256", sum))
            contentResolver.openInputStream(uri)!!.use { it.copyCounted(w.rawOut, size) { d -> progress(d, size) } }
            w.flush()
            w.recv().optBoolean("ok")
        }
        log("file", name, size, dev.optString("id"), deviceId(this), ok)
        return ok
    }

    // --- being controlled ---------------------------------------------------------
    private fun beControlled(w: Wire, dev: JSONObject) {
        val name = dev.optString("name")
        val decision = CompletableFuture<Intent?>()
        pendingDecision = decision
        askControl(name)
        val projectionData = try { decision.get(60, TimeUnit.SECONDS) } catch (e: Exception) { null }
        pendingDecision = null
        cancelNote(ASK_ID)
        val a11y = ControlAccessibilityService.instance
        if (projectionData == null || a11y == null) {
            w.send(JSONObject().put("t", "deny").put("msg", if (a11y == null) "remote control is not enabled on the phone" else "declined"))
            return
        }
        startForeground(NOTE_ID, statusNote("Being controlled by $name"),
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC or ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        val mpm = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        val projection = mpm.getMediaProjection(android.app.Activity.RESULT_OK, projectionData) ?: run {
            w.send(JSONObject().put("t", "deny").put("msg", "screen capture was not allowed")); return
        }
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        (getSystemService(WINDOW_SERVICE) as WindowManager).defaultDisplay.getRealMetrics(metrics)
        val streamer = ScreenStreamer(projection, metrics.widthPixels, metrics.heightPixels, metrics.densityDpi)
        val stopped = java.util.concurrent.atomic.AtomicBoolean(false)
        val stop = { stopped.set(true) }
        controlStop = stop
        a11y.beginSession(name, metrics.widthPixels, metrics.heightPixels) { stop() }
        w.send(JSONObject().put("t", "accept").put("w", metrics.widthPixels).put("h", metrics.heightPixels).put("kind", "phone"))
        log("control", name, 0, deviceId(this), dev.optString("id"), true)
        val reader = Thread {
            try {
                while (!stopped.get()) {
                    val h = w.recv()
                    when (h.optString("t")) {
                        "bye" -> break
                        "input" -> ControlAccessibilityService.instance?.handle(h)
                    }
                }
            } catch (e: Exception) { }
            stopped.set(true)
        }.apply { isDaemon = true; start() }
        try {
            while (!stopped.get()) {
                val t0 = System.currentTimeMillis()
                streamer.latestJpeg()?.let { w.send(JSONObject().put("t", "frame"), it) }
                val wait = 100 - (System.currentTimeMillis() - t0)
                if (wait > 0) Thread.sleep(wait)
            }
        } catch (e: Exception) {
        } finally {
            stopped.set(true)
            try { w.send(JSONObject().put("t", "bye")) } catch (e: Exception) { }
            streamer.close(); projection.stop()
            ControlAccessibilityService.instance?.endSession()
            controlStop = null
            reader.interrupt()
            startForeground(NOTE_ID, statusNote("Ready to receive from your devices"), ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        }
    }

    private fun askControl(name: String) {
        val i = Intent(this, ControlRequestActivity::class.java).putExtra("name", name)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        val pi = PendingIntent.getActivity(this, 1, i, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val n = Notification.Builder(this, CH_ALERT)
            .setSmallIcon(R.drawable.ic_link)
            .setContentTitle("$name wants to control this phone")
            .setContentText("Tap to allow or deny")
            .setCategory(Notification.CATEGORY_CALL)
            .setFullScreenIntent(pi, true)
            .setContentIntent(pi)
            .setAutoCancel(true)
            .build()
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).notify(ASK_ID, n)
    }

    // --- notifications ------------------------------------------------------------
    private fun channels() {
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        nm.createNotificationChannel(NotificationChannel(CH_STATUS, "Background", NotificationManager.IMPORTANCE_LOW))
        nm.createNotificationChannel(NotificationChannel(CH_ALERT, "Received and requests", NotificationManager.IMPORTANCE_HIGH))
    }

    private fun statusNote(text: String): Notification {
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        val b = Notification.Builder(this, CH_STATUS).setSmallIcon(R.drawable.ic_link)
            .setContentTitle("DriveWood Link").setContentText(text).setOngoing(true).setContentIntent(open)
        if (text.startsWith("Being controlled")) {
            val stop = PendingIntent.getService(this, 2, Intent(this, LinkService::class.java).setAction(ACTION_STOP_CONTROL),
                PendingIntent.FLAG_IMMUTABLE)
            b.addAction(Notification.Action.Builder(null, "Stop", stop).build())
        }
        return b.build()
    }

    private fun show(title: String, text: String, id: Int) {
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        val n = Notification.Builder(this, CH_ALERT).setSmallIcon(R.drawable.ic_link).setContentTitle(title)
            .setContentText(text).setStyle(Notification.BigTextStyle().bigText(text)).setAutoCancel(true)
            .setContentIntent(open).build()
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).notify(id, n)
    }

    private fun cancelNote(id: Int) = (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).cancel(id)

    companion object {
        @Volatile var instance: LinkService? = null
        const val NOTE_ID = 1; const val ASK_ID = 9
        const val CH_STATUS = "status"; const val CH_ALERT = "alerts"
        const val ACTION_STOP_CONTROL = "org.drivewood.link.STOP_CONTROL"

        /** Signed in and running somewhere (checked in during the last 2.5 minutes), even if not on this network. */
        fun seenRecently(d: JSONObject): Boolean = try {
            val t = java.time.OffsetDateTime.parse(d.optString("last_seen").replace(" ", "T"))
            java.time.Duration.between(t, java.time.OffsetDateTime.now()).seconds < 150
        } catch (e: Exception) { false }

        fun prefs(c: Context) = c.getSharedPreferences("device", Context.MODE_PRIVATE)
        fun deviceId(c: Context): String? = prefs(c).getString("id", null)
        fun deviceName(c: Context): String = prefs(c).getString("name", "Phone")!!

        fun heartbeat(c: Context, supa: Supa) {
            val id = deviceId(c) ?: return
            supa.rest("PATCH", "devices?id=eq.$id", JSONObject().put("lan_addr", localIp())
                .put("last_seen", "now()").put("cert_sha256", Identity.fingerprint()))
        }

        fun register(c: Context, supa: Supa, name: String) {
            val row = JSONObject().put("name", name.trim().take(40).ifEmpty { "Phone" }).put("kind", "phone")
                .put("cert_sha256", Identity.fingerprint()).put("lan_addr", localIp())
            val existing = deviceId(c)
            val r = if (existing != null) supa.rest("PATCH", "devices?id=eq.$existing", row, "return=representation") as JSONArray
                    else JSONArray()
            val saved = if (r.length() > 0) r else supa.rest("POST", "devices", row, "return=representation") as JSONArray
            val d = saved.getJSONObject(0)
            prefs(c).edit().putString("id", d.getString("id")).putString("name", d.getString("name")).apply()
        }

        fun forgetDevice(c: Context) = prefs(c).edit().clear().apply()
    }
}

/** Mirrors the screen into an ImageReader and hands out the newest frame as JPEG. */
class ScreenStreamer(projection: MediaProjection, realW: Int, realH: Int, dpi: Int) {
    private val scale = minOf(1f, 720f / minOf(realW, realH))
    private val w = (realW * scale).toInt() / 2 * 2
    private val h = (realH * scale).toInt() / 2 * 2
    private val thread = HandlerThread("dw-capture").apply { start() }
    private val reader = ImageReader.newInstance(w, h, PixelFormat.RGBA_8888, 2)
    private val display: VirtualDisplay?
    @Volatile private var latest: ByteArray? = null

    init {
        projection.registerCallback(object : MediaProjection.Callback() {}, Handler(thread.looper))
        display = projection.createVirtualDisplay("dw-link", w, h, dpi, DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            reader.surface, null, Handler(thread.looper))
        reader.setOnImageAvailableListener({ r ->
            val img = r.acquireLatestImage() ?: return@setOnImageAvailableListener
            try {
                val plane = img.planes[0]
                val rowPad = plane.rowStride - plane.pixelStride * w
                val bmp = Bitmap.createBitmap(w + rowPad / plane.pixelStride, h, Bitmap.Config.ARGB_8888)
                bmp.copyPixelsFromBuffer(plane.buffer)
                val cropped = if (rowPad > 0) Bitmap.createBitmap(bmp, 0, 0, w, h) else bmp
                val out = ByteArrayOutputStream()
                cropped.compress(Bitmap.CompressFormat.JPEG, 60, out)
                latest = out.toByteArray()
            } finally { img.close() }
        }, Handler(thread.looper))
    }

    fun latestJpeg(): ByteArray? = latest.also { latest = null }

    fun close() {
        display?.release(); reader.close(); thread.quitSafely()
    }
}

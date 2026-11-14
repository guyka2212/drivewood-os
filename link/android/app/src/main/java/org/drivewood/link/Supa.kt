package org.drivewood.link

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

object Config {
    const val SUPABASE_URL = "https://vknultzvokyblinqsxxs.supabase.co"
    // Publishable key: safe to ship, all data is protected by row-level security.
    const val SUPABASE_KEY = "sb_publishable_VOv_rXsKlq2eGob72IKvaQ_QhajzIjQ"
    const val TERMS_VERSION = "1.0"
    const val PRIVACY_VERSION = "1.0"
    const val TCP_PORT = 47800
    const val UDP_PORT = 47801
    const val APP_ID = "dwlink"
    const val PROTOCOL = 1
}

class SupaException(msg: String) : Exception(msg)

/** Minimal Supabase Auth + REST client. Network calls: never on the main thread. */
class Supa(ctx: Context) {
    private val prefs = ctx.getSharedPreferences("session", Context.MODE_PRIVATE)

    val userId: String? get() = prefs.getString("user_id", null)
    val signedIn: Boolean get() = prefs.getString("refresh_token", null) != null

    private fun request(method: String, path: String, body: Any? = null, token: String? = null,
                        prefer: String? = null): Any? {
        val c = URL(Config.SUPABASE_URL + path).openConnection() as HttpURLConnection
        try {
            c.requestMethod = method  // Android's HttpURLConnection supports PATCH
            c.connectTimeout = 15000; c.readTimeout = 15000
            c.setRequestProperty("apikey", Config.SUPABASE_KEY)
            c.setRequestProperty("Content-Type", "application/json")
            if (token != null) c.setRequestProperty("Authorization", "Bearer $token")
            if (prefer != null) c.setRequestProperty("Prefer", prefer)
            if (body != null) {
                c.doOutput = true
                c.outputStream.use { it.write(body.toString().toByteArray()) }
            }
            val code = c.responseCode
            val text = (if (code >= 400) c.errorStream else c.inputStream)?.bufferedReader()?.readText() ?: ""
            if (code >= 400) {
                val msg = try {
                    val j = JSONObject(text)
                    j.optString("msg").ifEmpty { j.optString("message") }.ifEmpty { j.optString("error_description") }.ifEmpty { text }
                } catch (e: Exception) { text.ifEmpty { "Error $code" } }
                throw SupaException(msg)
            }
            if (text.isBlank()) return null
            return if (text.trimStart().startsWith("[")) JSONArray(text) else JSONObject(text)
        } catch (e: java.io.IOException) {
            throw SupaException("No connection to the account server")
        } finally {
            c.disconnect()
        }
    }

    private fun store(s: JSONObject) {
        prefs.edit()
            .putString("access_token", s.getString("access_token"))
            .putString("refresh_token", s.getString("refresh_token"))
            .putLong("expires_at", System.currentTimeMillis() / 1000 + s.optLong("expires_in", 3600) - 60)
            .putString("user_id", s.getJSONObject("user").getString("id"))
            .apply()
    }

    /** true = signed in now, false = must confirm the email first. */
    fun signUp(email: String, password: String, username: String): Boolean {
        val data = JSONObject()
            .put("username", username.lowercase())
            .put("age_confirmed", "true").put("accepted_legal", "true")
            .put("terms_version", Config.TERMS_VERSION).put("privacy_version", Config.PRIVACY_VERSION)
        val r = request("POST", "/auth/v1/signup",
            JSONObject().put("email", email).put("password", password).put("data", data)) as JSONObject
        if (r.has("access_token")) { store(r); return true }
        return false
    }

    fun signIn(email: String, password: String) {
        store(request("POST", "/auth/v1/token?grant_type=password",
            JSONObject().put("email", email).put("password", password)) as JSONObject)
    }

    fun signOut() {
        try { request("POST", "/auth/v1/logout", JSONObject(), token()) } catch (e: Exception) { }
        prefs.edit().clear().apply()
    }

    @Synchronized
    fun token(): String {
        val refresh = prefs.getString("refresh_token", null) ?: throw SupaException("Not signed in")
        if (System.currentTimeMillis() / 1000 >= prefs.getLong("expires_at", 0)) {
            store(request("POST", "/auth/v1/token?grant_type=refresh_token",
                JSONObject().put("refresh_token", refresh)) as JSONObject)
        }
        return prefs.getString("access_token", "")!!
    }

    fun rest(method: String, path: String, body: Any? = null, prefer: String? = null): Any? =
        request(method, "/rest/v1/$path", body, token(), prefer)

    fun rpc(name: String, args: JSONObject = JSONObject()) = rest("POST", "rpc/$name", args)

    companion object {
        /** Which user owns this access token? Used to check devices that connect to us. */
        fun verifyToken(token: String): String? = try {
            val c = URL(Config.SUPABASE_URL + "/auth/v1/user").openConnection() as HttpURLConnection
            c.setRequestProperty("apikey", Config.SUPABASE_KEY)
            c.setRequestProperty("Authorization", "Bearer $token")
            c.connectTimeout = 10000; c.readTimeout = 10000
            if (c.responseCode == 200) JSONObject(c.inputStream.bufferedReader().readText()).optString("id") else null
        } catch (e: Exception) { null }
    }
}

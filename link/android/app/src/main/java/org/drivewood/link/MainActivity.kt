package org.drivewood.link

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.EditText
import android.widget.LinearLayout
import android.graphics.Color
import org.drivewood.link.Ui.bg
import org.drivewood.link.Ui.button
import org.drivewood.link.Ui.card
import org.drivewood.link.Ui.column
import org.drivewood.link.Ui.consent
import org.drivewood.link.Ui.dp
import org.drivewood.link.Ui.enter
import org.drivewood.link.Ui.pulse
import org.drivewood.link.Ui.spin
import org.drivewood.link.Ui.field
import org.drivewood.link.Ui.row
import org.drivewood.link.Ui.scroll
import org.drivewood.link.Ui.showDoc
import org.drivewood.link.Ui.text
import org.drivewood.link.Ui.title
import org.drivewood.link.Ui.toast
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : Activity() {
    private lateinit var supa: Supa
    private var tab = "devices"
    private var pendingTarget: JSONObject? = null
    private var username = ""
    private var refreshing = false
    private val listener = { runOnUiThread { if (tab == "devices" && !isFinishing && !refreshing) showMain(animate = false) } }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        supa = Supa(this)
        hideStatusBar()
        if (Build.VERSION.SDK_INT >= 33) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        route()
    }

    override fun onDestroy() { LinkService.instance?.removeListener(listener); super.onDestroy() }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) hideStatusBar()
    }

    /** Hide the top status bar (time, notifications); swipe down to peek at it. */
    private fun hideStatusBar() {
        window.decorView  // make sure the window exists before asking for its insets controller
        if (Build.VERSION.SDK_INT >= 30) {
            window.insetsController?.let {
                it.hide(android.view.WindowInsets.Type.statusBars())
                it.systemBarsBehavior = android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }
        } else {
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_FULLSCREEN or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        }
    }

    private fun route() {
        if (!supa.signedIn) return showSignIn()
        bg({
            val p = supa.rest("GET", "profiles?id=eq.${supa.userId}&select=username,terms_version,privacy_version") as JSONArray
            if (p.length() == 0) null else p.getJSONObject(0)
        }, { p ->
            when {
                p == null -> { supa.signOut(); showSignIn() }
                p.optString("terms_version") != Config.TERMS_VERSION || p.optString("privacy_version") != Config.PRIVACY_VERSION -> showReaccept()
                LinkService.deviceId(this) == null -> { username = p.optString("username"); showName() }
                else -> { username = p.optString("username"); startService(); showMain() }
            }
        }, { toast(it); showSignIn() })
    }

    private fun startService() {
        startForegroundService(Intent(this, LinkService::class.java))
        window.decorView.postDelayed({ LinkService.instance?.addListener(listener) }, 500)
    }

    // --- sign in / sign up ----------------------------------------------------------
    private fun showSignIn(message: String = "") {
        val c = column()
        c.addView(title("DriveWood Link"))
        c.addView(text("Send files and get controlled by your own computers.", 15f, Ui.MUTED))
        val email = field("Email", email = true); val pass = field("Password", password = true)
        val err = text(message, 14f, Ui.RED)
        c.addView(email); c.addView(pass)
        c.addView(button("Sign in", primary = true) {
            err.text = "Signing in…"
            bg({ supa.signIn(email.text.toString().trim(), pass.text.toString()) }, { route() }, { err.text = it })
        })
        c.addView(err)
        c.addView(button("Create an account") { showSignUp() })
        setContentView(scroll(c))
    }

    private fun showSignUp() {
        val c = column()
        c.addView(title("Create your account"))
        val email = field("Email", email = true)
        val user = field("Username (a-z, 0-9, _)")
        val pass = field("Password (8+ characters)", password = true)
        val err = text("", 14f, Ui.RED)
        lateinit var create: View
        c.addView(email); c.addView(user); c.addView(pass)
        c.addView(consent { create.isEnabled = it; create.alpha = if (it) 1f else 0.4f })
        create = button("Create account", primary = true) {
            val e = email.text.toString().trim(); val u = user.text.toString().trim().lowercase(); val p = pass.text.toString()
            when {
                !Regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$").matches(e) -> err.text = "Enter a valid email address."
                !Regex("^[a-z0-9_]{3,24}$").matches(u) -> err.text = "Username: 3–24 characters, a–z, 0–9 or _."
                p.length < 8 -> err.text = "Password must be at least 8 characters."
                else -> {
                    err.text = "Creating your account…"
                    bg({ supa.signUp(e, p, u) }, { signedIn ->
                        if (signedIn) route() else showSignIn("Account created. Open the link we emailed you, then sign in.")
                    }, { err.text = it })
                }
            }
        }.apply { isEnabled = false; alpha = 0.4f }
        c.addView(create); c.addView(err)
        c.addView(button("I already have an account") { showSignIn() })
        setContentView(scroll(c))
    }

    private fun showReaccept() {
        val c = column()
        c.addView(title("Updated Terms and Privacy Policy"))
        c.addView(text("Please read and accept them to keep using DriveWood Link. If you don't agree, you can export your data and delete your account.", 15f, Ui.MUTED))
        lateinit var go: View
        c.addView(consent { go.isEnabled = it; go.alpha = if (it) 1f else 0.4f })
        go = button("Accept and continue", primary = true) {
            bg({ supa.rpc("accept_legal", JSONObject().put("terms", Config.TERMS_VERSION).put("privacy", Config.PRIVACY_VERSION)) }, { route() })
        }.apply { isEnabled = false; alpha = 0.4f }
        c.addView(go)
        c.addView(button("Export my data") { exportData() })
        c.addView(button("Delete my account", danger = true) { deleteAccount() })
        setContentView(scroll(c))
    }

    private fun showName() {
        val c = column()
        c.addView(title("Name this phone"))
        c.addView(text("Your other devices will see this name.", 15f, Ui.MUTED))
        val name = field("Device name").apply { setText(LinkService.deviceName(this@MainActivity).takeIf { it != "Phone" } ?: Build.MODEL) }
        c.addView(name)
        c.addView(button("Continue", primary = true) {
            bg({ LinkService.register(this, supa, name.text.toString()) }, { startService(); showMain() })
        })
        setContentView(scroll(c))
    }

    // --- main -------------------------------------------------------------------------
    private fun showMain(animate: Boolean = true) {
        val c = column(16)
        val tabs = row()
        for ((id, label) in listOf("devices" to "Devices", "history" to "History", "account" to "Account")) {
            tabs.addView(button(label, primary = tab == id) { tab = id; showMain() }.apply {
                layoutParams = LinearLayout.LayoutParams(0, -2, 1f).apply { marginEnd = dp(4) }
            })
        }
        c.addView(tabs)
        when (tab) {
            "devices" -> devicesTab(c)
            "history" -> historyTab(c)
            else -> accountTab(c)
        }
        setContentView(scroll(c))
        if (animate) enter(c)
    }

    private fun devicesTab(c: LinearLayout) {
        val svc = LinkService.instance
        val others = svc?.others() ?: emptyList()
        if (others.isEmpty()) c.addView(text("No other devices yet. Sign in to DriveWood Link on your Drivewood computer with the same account.", 15f, Ui.MUTED))
        for (d in others) {
            val on = svc?.isOnline(d) == true
            val elsewhere = !on && LinkService.seenRecently(d)
            val k = card()
            val head = row()
            val dot = text("●  ", 16f, if (on) Ui.ON else if (elsewhere) Ui.SAND else Color.parseColor("#46524D"))
            head.addView(dot)
            if (on) pulse(dot)
            head.addView(text(d.optString("name"), 17f, Ui.TEXT, true))
            k.addView(head)
            k.addView(text((if (d.optString("kind") == "phone") "Phone" else "Computer") + when {
                on -> " · nearby, ready to send"
                elsewhere -> " · online, but on another network (connect both to the same Wi-Fi)"
                else -> " · offline"
            }, 13f, Ui.MUTED))
            if (on) {
                k.addView(button("Send files") { pendingTarget = d; pickFiles() })
                k.addView(button("Send text") { askText(d) })
            }
            c.addView(k)
        }
        val icon = text("⟳", 22f, Ui.ACCENT, true).apply { setPadding(0, 0, dp(10), 0) }
        val refresh = row().apply {
            gravity = android.view.Gravity.CENTER
            background = Ui.run { rounded(Ui.CARD2) }
            setPadding(dp(14), dp(10), dp(14), dp(10))
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) }
            addView(icon); addView(text("Refresh", 15f, Ui.TEXT))
            Ui.pressAnimation(this)
        }
        refresh.setOnClickListener {
            if (refreshing) return@setOnClickListener
            refreshing = true
            val anim = spin(icon)
            bg({ LinkService.instance?.let { s -> LinkService.heartbeat(this, s.supa); s.refreshDevices() }; Thread.sleep(400) },
                { anim.cancel(); refreshing = false; showMain() }, { anim.cancel(); refreshing = false; toast(it) })
        }
        c.addView(refresh)
        c.addView(text("Computers can take control of this phone. Each time, you'll be asked first.", 13f, Ui.MUTED))
    }

    private fun historyTab(c: LinearLayout) {
        val list = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        c.addView(list)
        val names = (LinkService.instance?.devices ?: emptyList()).associate { it.optString("id") to it.optString("name") }
        bg({ supa.rest("GET", "transfers?select=kind,name,size,ok,created_at,from_device,to_device&order=created_at.desc&limit=200") as JSONArray }, { arr ->
            if (arr.length() == 0) list.addView(text("Nothing sent yet.", 15f, Ui.MUTED))
            for (i in 0 until arr.length()) {
                val r = arr.getJSONObject(i)
                val k = card()
                val what = mapOf("file" to "File", "text" to "Text", "clipboard" to "Clipboard", "control" to "Remote control")[r.optString("kind")]
                k.addView(text("$what: ${r.optString("name")}"))
                k.addView(text("${names[r.optString("from_device")] ?: "?"} → ${names[r.optString("to_device")] ?: "?"} · ${r.optString("created_at").take(16).replace('T', ' ')}" +
                        if (!r.optBoolean("ok")) " · failed" else "", 13f, Ui.MUTED))
                list.addView(k)
            }
        })
        c.addView(button("Clear history") { bg({ supa.rest("DELETE", "transfers?owner=eq.${supa.userId}") }, { showMain() }) })
    }

    private fun accountTab(c: LinearLayout) {
        c.addView(text("Signed in as $username\nThis phone: ${LinkService.deviceName(this)}", 15f, Ui.MUTED))
        val a11y = ControlAccessibilityService.instance != null
        c.addView(text(if (a11y) "Remote control: ready" else "Remote control: off. Turn on \"DriveWood Link remote control\" in Accessibility so your computers can control this phone.", 14f, if (a11y) Ui.ON else Ui.MUTED))
        if (!a11y) c.addView(button("Open Accessibility settings") { startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) })
        c.addView(button("Rename this phone") { showName() })
        c.addView(button("Export my data (JSON)") { exportData() })
        c.addView(button("Terms of Use") { showDoc("TERMS.md") })
        c.addView(button("Privacy Policy") { showDoc("PRIVACY.md") })
        // Sign out keeps this phone in your device list (offline); signing in again reuses it.
        c.addView(button("Sign out") { bg({ supa.signOut() }, { afterSignOut(forget = false) }) })
        c.addView(button("Remove this device", danger = true) { removeThisDevice() })
        c.addView(button("Delete my account", danger = true) { deleteAccount() })
    }

    private fun afterSignOut(forget: Boolean = true) {
        stopService(Intent(this, LinkService::class.java))
        if (forget) { LinkService.forgetDevice(this); Identity.reset() }
        tab = "devices"
        showSignIn()
    }

    /** Remove this phone from the account: other devices stop seeing it, then sign out here. */
    private fun removeThisDevice() {
        val name = LinkService.deviceName(this)
        AlertDialog.Builder(this).setTitle("Remove $name from your account?")
            .setMessage("Your other devices will stop seeing it, and it will be signed out. Your account and your other devices are not affected.")
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Remove device") { _, _ ->
                bg({
                    LinkService.deviceId(this)?.let { supa.rest("DELETE", "devices?id=eq.$it") }
                    supa.signOut()
                }, { afterSignOut(forget = true); toast("$name was removed") })
            }.show()
    }

    private fun deleteAccount() {
        AlertDialog.Builder(this).setTitle("Delete your account?")
            .setMessage("Your account, devices and history are deleted permanently. This can't be undone.")
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Delete account") { _, _ ->
                bg({ supa.rpc("delete_my_account"); supa.signOut() }, { afterSignOut() })
            }.show()
    }

    // --- sending ----------------------------------------------------------------------
    private fun pickFiles() {
        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE)
            .putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true), REQ_FILES)
    }

    private fun askText(d: JSONObject) {
        val input = EditText(this).apply { minLines = 3 }
        AlertDialog.Builder(this).setTitle("Text to ${d.optString("name")}").setView(input)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Send") { _, _ ->
                val t = input.text.toString()
                if (t.isNotBlank()) bg({ LinkService.instance!!.sendText(d, t) }, { toast(if (it) "Sent" else "Failed") })
            }.show()
    }

    private fun exportData() = startActivityForResult(Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json")
        .addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE, "drivewood-link-data.json"), REQ_EXPORT)

    @Deprecated("simple and dependency-free")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode != RESULT_OK || data == null) return
        when (requestCode) {
            REQ_FILES -> {
                val target = pendingTarget ?: return
                val uris = mutableListOf<Uri>()
                data.clipData?.let { cd -> for (i in 0 until cd.itemCount) uris.add(cd.getItemAt(i).uri) } ?: data.data?.let { uris.add(it) }
                sendUris(this, target, uris)
            }
            REQ_EXPORT -> {
                val uri = data.data ?: return
                bg({
                    val out = JSONObject()
                        .put("profile", supa.rest("GET", "profiles?select=*"))
                        .put("devices", supa.rest("GET", "devices?select=*"))
                        .put("history", supa.rest("GET", "transfers?select=*"))
                    contentResolver.openOutputStream(uri)!!.use { it.write(out.toString(2).toByteArray()) }
                }, { toast("Exported") })
            }
        }
    }

    companion object {
        const val REQ_FILES = 10; const val REQ_EXPORT = 11

        fun sendUris(a: Activity, target: JSONObject, uris: List<Uri>) {
            val svc = LinkService.instance ?: return a.toast("DriveWood Link isn't running. Open the app and sign in.")
            a.toast("Sending ${uris.size} file(s) to ${target.optString("name")}…")
            a.bg({ uris.count { svc.sendFile(target, it) } }, { ok ->
                a.toast(if (ok == uris.size) "Sent to ${target.optString("name")}" else "${uris.size - ok} file(s) failed")
            })
        }
    }
}

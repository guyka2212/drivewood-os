package org.drivewood.link

import android.app.Activity
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import org.drivewood.link.Ui.button
import org.drivewood.link.Ui.column
import org.drivewood.link.Ui.text
import org.drivewood.link.Ui.title

/** Asks the phone owner before any computer can control the phone. */
class ControlRequestActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val name = intent.getStringExtra("name") ?: "A computer"
        val c = column()
        c.addView(title("$name wants to control this phone"))
        c.addView(text("They will see your screen and can tap and type. A banner with a Stop button stays on screen the whole time.", 15f, Ui.MUTED))
        if (ControlAccessibilityService.instance == null) {
            c.addView(text("First turn on \"DriveWood Link remote control\" in Accessibility, then ask again from the computer.", 15f, Ui.RED))
            c.addView(button("Open Accessibility settings", primary = true) {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)); answer(null)
            })
            c.addView(button("Deny") { answer(null) })
        } else {
            c.addView(button("Allow", primary = true) {
                val mpm = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
                startActivityForResult(mpm.createScreenCaptureIntent(), 1)
            })
            c.addView(button("Deny") { answer(null) })
        }
        setContentView(c)
        setFinishOnTouchOutside(false)
    }

    @Deprecated("simple and dependency-free")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        answer(if (resultCode == RESULT_OK) data else null)
    }

    private fun answer(data: Intent?) {
        LinkService.instance?.pendingDecision?.complete(data)
        finish()
    }

    @Deprecated("back = deny")
    override fun onBackPressed() = answer(null)
}

/** "Share → DriveWood Link" from any app: pick one of your online devices. */
class ShareActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val uris = mutableListOf<Uri>()
        @Suppress("DEPRECATION")
        when (intent.action) {
            Intent.ACTION_SEND -> (intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM))?.let { uris.add(it) }
            Intent.ACTION_SEND_MULTIPLE -> intent.getParcelableArrayListExtra<Uri>(Intent.EXTRA_STREAM)?.let { uris.addAll(it) }
        }
        val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
        val svc = LinkService.instance
        val c = column()
        c.addView(title("Send with DriveWood Link"))
        val online = svc?.others()?.filter { svc.isOnline(it) } ?: emptyList()
        if (svc == null) c.addView(text("Open DriveWood Link and sign in first.", 15f, Ui.MUTED))
        else if (online.isEmpty()) c.addView(text("None of your devices are online on this Wi-Fi.", 15f, Ui.MUTED))
        for (d in online) {
            c.addView(button(d.optString("name"), primary = true) {
                if (uris.isNotEmpty()) MainActivity.sendUris(this, d, uris)
                else if (!sharedText.isNullOrBlank()) Thread { try { svc!!.sendText(d, sharedText) } catch (e: Exception) { } }.start()
                finish()
            })
        }
        c.addView(button("Cancel") { finish() })
        setContentView(c)
    }
}

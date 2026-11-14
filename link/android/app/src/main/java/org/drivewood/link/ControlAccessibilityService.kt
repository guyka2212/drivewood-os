package org.drivewood.link

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Color
import android.graphics.Path
import android.graphics.PixelFormat
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import org.json.JSONObject

/** Turns the controlling computer's mouse and keyboard into touches and typing,
 *  only while a session the phone owner accepted is running. Shows a banner with Stop. */
class ControlAccessibilityService : AccessibilityService() {
    private val main = Handler(Looper.getMainLooper())
    private var active = false
    private var sw = 1; private var sh = 1
    private var banner: LinearLayout? = null
    private var stroke = mutableListOf<Pair<Float, Float>>()
    private var strokeStart = 0L
    private var lastX = 0.5f; private var lastY = 0.5f

    override fun onServiceConnected() { instance = this }
    override fun onDestroy() { instance = null; super.onDestroy() }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}

    fun beginSession(name: String, w: Int, h: Int, onStop: () -> Unit) {
        sw = w; sh = h; active = true
        main.post { showBanner(name, onStop) }
    }

    fun endSession() {
        active = false
        main.post { banner?.let { (getSystemService(WINDOW_SERVICE) as WindowManager).removeView(it) }; banner = null }
    }

    private fun showBanner(name: String, onStop: () -> Unit) {
        val wm = getSystemService(WINDOW_SERVICE) as WindowManager
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; setPadding(32, 16, 16, 16); gravity = Gravity.CENTER_VERTICAL
            setBackgroundColor(Color.parseColor("#EE4FD1B5"))
            addView(TextView(context).apply { text = "Being controlled by $name"; setTextColor(Color.parseColor("#06201A")); textSize = 14f })
            addView(Button(context).apply { text = "Stop"; setOnClickListener { onStop() } })
        }
        val lp = WindowManager.LayoutParams(WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE, PixelFormat.TRANSLUCENT).apply {
            gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL; y = 80
        }
        wm.addView(row, lp)
        banner = row
    }

    private fun px(e: JSONObject): Pair<Float, Float> {
        lastX = e.optDouble("x", lastX.toDouble()).toFloat().coerceIn(0f, 1f)
        lastY = e.optDouble("y", lastY.toDouble()).toFloat().coerceIn(0f, 1f)
        return lastX * (sw - 1) to lastY * (sh - 1)
    }

    fun handle(e: JSONObject) {
        if (!active) return
        when (e.optString("k")) {
            "move" -> { val p = px(e); if (stroke.isNotEmpty()) stroke.add(p) }
            "button" -> {
                val b = e.optInt("b", 1); val down = e.optBoolean("down")
                when {
                    b == 3 && down -> performGlobalAction(GLOBAL_ACTION_BACK)
                    b == 2 && down -> performGlobalAction(GLOBAL_ACTION_HOME)
                    b == 1 && down -> { stroke = mutableListOf(px(e)); strokeStart = System.currentTimeMillis() }
                    b == 1 && !down && stroke.isNotEmpty() -> { stroke.add(px(e)); playStroke() }
                }
            }
            "scroll" -> {
                val dy = e.optInt("dy", 0); val dx = e.optInt("dx", 0)
                if (dy == 0 && dx == 0) return
                val (x, y) = lastX * sw to lastY * sh
                val path = Path().apply { moveTo(x, y); lineTo((x - dx * sw * 0.15f).coerceIn(1f, sw - 1f), (y - dy * sh * 0.15f).coerceIn(1f, sh - 1f)) }
                gesture(path, 120)
            }
            "key" -> if (e.optBoolean("down")) key(e)
        }
    }

    private fun playStroke() {
        val pts = stroke; stroke = mutableListOf()
        val dur = (System.currentTimeMillis() - strokeStart).coerceIn(40, 5000)
        val path = Path().apply {
            moveTo(pts[0].first, pts[0].second)
            if (pts.size == 1 || pts.all { kotlin.math.abs(it.first - pts[0].first) < 8 && kotlin.math.abs(it.second - pts[0].second) < 8 })
                lineTo(pts[0].first + 1, pts[0].second + 1)  // a tap (or a long press if held)
            else pts.drop(1).forEach { lineTo(it.first, it.second) }
        }
        gesture(path, dur)
    }

    private fun gesture(path: Path, duration: Long) {
        dispatchGesture(GestureDescription.Builder().addStroke(GestureDescription.StrokeDescription(path, 0, duration)).build(), null, null)
    }

    private fun key(e: JSONObject) {
        when (e.optString("name")) {
            "Escape" -> return void(performGlobalAction(GLOBAL_ACTION_BACK))
            "Super_L", "Super_R", "Home" -> return void(performGlobalAction(GLOBAL_ACTION_HOME))
            "Tab" -> return void(performGlobalAction(GLOBAL_ACTION_RECENTS))
            "BackSpace" -> return editText { it.dropLast(1) }
            "Return", "KP_Enter" -> {
                val node = findFocus(AccessibilityNodeInfo.FOCUS_INPUT) ?: return
                node.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_IME_ENTER.id); return
            }
        }
        val ch = e.optString("char", "")
        if (ch.isNotEmpty() && ch != "null") editText { it + ch }
    }

    private fun editText(change: (String) -> String) {
        val node = findFocus(AccessibilityNodeInfo.FOCUS_INPUT) ?: return
        val current = if (node.isShowingHintText) "" else (node.text?.toString() ?: "")
        val args = Bundle().apply { putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, change(current)) }
        node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
    }

    private fun void(@Suppress("UNUSED_PARAMETER") b: Boolean) {}

    companion object { @Volatile var instance: ControlAccessibilityService? = null }
}

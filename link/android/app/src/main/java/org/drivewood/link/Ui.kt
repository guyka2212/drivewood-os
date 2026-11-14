package org.drivewood.link

import android.app.Activity
import android.app.AlertDialog
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import java.util.concurrent.Executors

/** Small helpers so the screens can be built in code with the Drivewood look. */
object Ui {
    // Sea-glass theme (same as the desktop app)
    val BG = Color.parseColor("#0F1513")
    val CARD = Color.parseColor("#161F1C")
    val CARD2 = Color.parseColor("#1D2925")
    val TEXT = Color.parseColor("#E6EBE7")
    val MUTED = Color.parseColor("#8FA199")
    val ACCENT = Color.parseColor("#4FD1B5")
    val ON_ACCENT = Color.parseColor("#06201A")
    val SAND = Color.parseColor("#D8C9A3")
    val RED = Color.parseColor("#FF8F8F")
    val ON = ACCENT
    private val pool = Executors.newCachedThreadPool()

    fun <T> Activity.bg(work: () -> T, done: (T) -> Unit, fail: (String) -> Unit = { toast(it) }) {
        pool.execute {
            try { val r = work(); runOnUiThread { if (!isFinishing) done(r) } }
            catch (e: Exception) { runOnUiThread { if (!isFinishing) fail(e.message ?: e.toString()) } }
        }
    }

    fun Activity.toast(msg: String) = android.widget.Toast.makeText(this, msg, android.widget.Toast.LENGTH_LONG).show()

    fun Activity.dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    fun Activity.column(pad: Int = 24): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL; setPadding(dp(pad), dp(pad) + dp(36), dp(pad), dp(pad)); setBackgroundColor(BG)
    }

    fun Activity.scroll(child: View) = ScrollView(this).apply { setBackgroundColor(BG); isFillViewport = true; addView(child) }

    fun Activity.text(s: String, size: Float = 15f, color: Int = TEXT, bold: Boolean = false) = TextView(this).apply {
        text = s; textSize = size; setTextColor(color); if (bold) typeface = Typeface.DEFAULT_BOLD
        setPadding(0, dp(4), 0, dp(4))
    }

    fun Activity.title(s: String) = text(s, 24f, TEXT, true).apply { setPadding(0, dp(8), 0, dp(8)) }

    fun Activity.field(hint: String, password: Boolean = false, email: Boolean = false) = EditText(this).apply {
        this.hint = hint; setTextColor(TEXT); setHintTextColor(MUTED); textSize = 16f; isSingleLine = true
        inputType = when {
            password -> InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            email -> InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS
            else -> InputType.TYPE_CLASS_TEXT
        }
        background = rounded(CARD2); setPadding(dp(14), dp(12), dp(14), dp(12))
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) }
        setOnFocusChangeListener { v, f -> v.animate().scaleX(if (f) 1.015f else 1f).scaleY(if (f) 1.015f else 1f).setDuration(150).start() }
    }

    fun Activity.button(s: String, primary: Boolean = false, danger: Boolean = false, onClick: () -> Unit) = Button(this).apply {
        text = s; isAllCaps = false; textSize = 15f
        setTextColor(if (primary) ON_ACCENT else if (danger) RED else TEXT)
        if (primary) typeface = Typeface.DEFAULT_BOLD
        background = rounded(if (primary) ACCENT else CARD2)
        stateListAnimator = null
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) }
        pressAnimation(this)
        setOnClickListener { onClick() }
    }

    /** Buttons shrink a little while pressed and spring back. */
    @android.annotation.SuppressLint("ClickableViewAccessibility")
    fun pressAnimation(v: View) = v.setOnTouchListener { view, e ->
        when (e.actionMasked) {
            android.view.MotionEvent.ACTION_DOWN -> view.animate().scaleX(0.96f).scaleY(0.96f).setDuration(90).start()
            android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL ->
                view.animate().scaleX(1f).scaleY(1f).setDuration(160)
                    .setInterpolator(android.view.animation.OvershootInterpolator(2f)).start()
        }
        false
    }

    /** Children slide up and fade in one after another. */
    fun enter(root: android.view.ViewGroup, step: Long = 45) {
        for (i in 0 until root.childCount) {
            val c = root.getChildAt(i)
            c.alpha = 0f; c.translationY = 40f
            c.animate().alpha(1f).translationY(0f).setStartDelay(i * step).setDuration(280)
                .setInterpolator(android.view.animation.DecelerateInterpolator(1.6f)).start()
        }
    }

    /** Gentle breathing for the "nearby" dot. */
    fun pulse(v: View) = android.animation.ObjectAnimator.ofFloat(v, "alpha", 1f, 0.3f).apply {
        duration = 800; repeatMode = android.animation.ValueAnimator.REVERSE
        repeatCount = android.animation.ValueAnimator.INFINITE; start()
    }

    /** A spinning ⟳ while something loads. */
    fun spin(v: View) = android.animation.ObjectAnimator.ofFloat(v, "rotation", 0f, 360f).apply {
        duration = 800; repeatCount = android.animation.ValueAnimator.INFINITE
        interpolator = android.view.animation.LinearInterpolator(); start()
    }

    fun Activity.rounded(color: Int) = GradientDrawable().apply { setColor(color); cornerRadius = dp(12).toFloat() }

    fun Activity.card(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL; background = rounded(CARD); setPadding(dp(14), dp(12), dp(14), dp(12))
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) }
    }

    fun Activity.row(): LinearLayout = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }

    fun Activity.showDoc(asset: String) {
        val body = cleanMarkdown(assets.open(asset).bufferedReader().readText())
        AlertDialog.Builder(this).setTitle(if (asset.startsWith("TERMS")) "Terms of Use" else "Privacy Policy")
            .setMessage(body).setPositiveButton("Close", null).show()
    }

    /** Legal Markdown -> readable text: headings in bold, paragraphs joined, tables as bullet lines. */
    fun cleanMarkdown(md: String): CharSequence {
        val sb = android.text.SpannableStringBuilder()
        val para = mutableListOf<String>()
        fun bold(s: String, scale: Float = 1f) {
            val start = sb.length; sb.append(s)
            sb.setSpan(android.text.style.StyleSpan(Typeface.BOLD), start, sb.length, 0)
            if (scale != 1f) sb.setSpan(android.text.style.RelativeSizeSpan(scale), start, sb.length, 0)
        }
        fun inline(s: String) = s.split("**").forEachIndexed { i, part -> if (i % 2 == 1) bold(part) else sb.append(part) }
        fun flush() { if (para.isNotEmpty()) { inline(para.joinToString(" ")); sb.append("\n\n"); para.clear() } }
        for (raw in md.lines()) {
            val line = raw.trim().replace("`", "")
            when {
                line.isEmpty() -> flush()
                line.startsWith("# ") -> { flush(); bold(line.drop(2) + "\n\n", 1.3f) }
                line.startsWith("## ") -> { flush(); bold(line.drop(3) + "\n", 1.1f) }
                line.startsWith("|") -> {
                    flush()
                    val cells = line.trim('|').split("|").map { it.trim() }
                    if (!cells.all { c -> c.all { it in "-: " } }) { sb.append("•  "); inline(cells.joinToString("  —  ")); sb.append("\n") }
                }
                line.startsWith("- ") -> { flush(); sb.append("•  "); inline(line.drop(2)); sb.append("\n") }
                Regex("^\\d+\\. ").containsMatchIn(line) -> { flush(); inline(line); sb.append("\n") }
                else -> para.add(line)
            }
        }
        flush()
        return sb
    }

    /** Unticked consent checkbox with links to both documents. */
    fun Activity.consent(onChange: (Boolean) -> Unit): LinearLayout {
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(0, dp(12), 0, 0) }
        val check = CheckBox(this).apply {
            text = "I am at least 13 (16 in the EEA/UK) and I agree to the Terms of Use and the Privacy Policy"
            setTextColor(TEXT); isChecked = false
            buttonTintList = android.content.res.ColorStateList.valueOf(ACCENT)
            setOnCheckedChangeListener { _, on -> onChange(on) }
        }
        val links = row()
        links.addView(text("Read: ", 14f, MUTED))
        links.addView(text("Terms of Use", 14f, ACCENT).apply { setOnClickListener { showDoc("TERMS.md") }; setPadding(dp(4), dp(8), dp(12), dp(8)) })
        links.addView(text("Privacy Policy", 14f, ACCENT).apply { setOnClickListener { showDoc("PRIVACY.md") }; setPadding(dp(4), dp(8), dp(4), dp(8)) })
        box.addView(check); box.addView(links)
        return box
    }
}

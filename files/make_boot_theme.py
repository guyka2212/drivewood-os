"""Plymouth theme that plays the recorded screensaver animation (matrix rain resolving
into DRIFTWOOD) frame by frame, then holds the finished word with a gentle pulse."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "plymouth", "driftwood-boot")
frames = sorted(f for f in os.listdir(D) if f.startswith("f") and f.endswith(".png"))
N = len(frames)
names = "\n".join(f'names[{i}] = "{name}";' for i, name in enumerate(frames))

script = f"""# Driftwood boot screen: the screensaver's rain resolving into DRIFTWOOD.
Window.SetBackgroundTopColor(0, 0, 0);
Window.SetBackgroundBottomColor(0, 0, 0);

global.N = {N};
global.FW = 1100;
global.FH = 360;
{names}

global.frame = 0;
global.shown = -1;
global.layout_width = 0;
global.layout_height = 0;
anim.sprite = Sprite();
pw.sprite = Sprite();
pw.sprite.SetOpacity(0);

fun layout() {{
  global.layout_width = Window.GetWidth();
  global.layout_height = Window.GetHeight();
  global.ax = Math.Int(global.layout_width / 2 - global.FW / 2);
  global.ay = Math.Int(global.layout_height / 2 - global.FH / 2);
  anim.sprite.SetPosition(global.ax, global.ay, 5);
}}

fun refresh_callback() {{
  if (Window.GetWidth() != global.layout_width || Window.GetHeight() != global.layout_height) layout();
  global.frame++;
  # 50 refreshes a second, 30 animation frames a second
  idx = Math.Int(global.frame * 30 / 50);
  if (idx >= global.N) {{
    idx = global.N - 1;
    anim.sprite.SetOpacity(0.86 + 0.14 * Math.Sin(global.frame / 22));
  }}
  if (idx != global.shown) {{
    anim.image = Image(names[idx]);
    anim.sprite.SetImage(anim.image);
    global.shown = idx;
  }}
}}
Plymouth.SetRefreshFunction(refresh_callback);

# disk-unlock prompt, shown under the animation if the disk asks for one
fun display_password_callback(prompt, bullets) {{
  dots = "";
  for (i = 0; i < bullets && i < 24; i++) dots = dots + "*";
  pw.image = Image.Text(prompt + "  " + dots, 0.56, 0.71, 0.90, 1, "Cantarell 14");
  pw.sprite.SetImage(pw.image);
  pw.sprite.SetPosition(global.layout_width / 2 - pw.image.GetWidth() / 2, global.ay + global.FH + 30, 20);
  pw.sprite.SetOpacity(1);
}}
fun display_normal_callback() {{
  pw.sprite.SetOpacity(0);
}}
Plymouth.SetDisplayPasswordFunction(display_password_callback);
Plymouth.SetDisplayNormalFunction(display_normal_callback);

message_sprite = Sprite();
message_sprite.SetPosition(10, 10, 10000);
fun display_message_callback(text) {{
  message_sprite.SetImage(Image.Text(text, 0.45, 0.50, 0.58));
  message_sprite.SetOpacity(1);
}}
fun hide_message_callback(text) {{
  message_sprite.SetOpacity(0);
}}
Plymouth.SetDisplayMessageFunction(display_message_callback);
Plymouth.SetHideMessageFunction(hide_message_callback);

layout();
"""
open(os.path.join(D, "driftwood.script"), "w", newline="\n").write(script)
open(os.path.join(D, "driftwood.plymouth"), "w", newline="\n").write("""[Plymouth Theme]
Name=Driftwood
Description=Rain resolving into DRIFTWOOD, the screensaver animation.
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/driftwood
ScriptFile=/usr/share/plymouth/themes/driftwood/driftwood.script
ConsoleLogBackgroundColor=0x000000
MonospaceFont=Cantarell 11
Font=Cantarell 11
""")
open(os.path.join(D, "files.txt"), "w", newline="\n").write("\n".join(frames + ["driftwood.script", "driftwood.plymouth"]) + "\n")
print("frames:", N)

-- Drivewood desktop (Hyprland 0.57, Lua config).
-- Your own changes go in ~/.config/hypr/custom.lua (loaded last, never overwritten).

local home = os.getenv("HOME")
local shell = "qs -p /usr/share/drivewood/shell ipc call drivewood "

hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })

hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("GDK_BACKEND", "wayland,x11")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")

-- ---- look ----------------------------------------------------------------
hl.config({
  general = {
    gaps_in = 6,
    gaps_out = 12,
    border_size = 2,
    col = {
      active_border = { colors = { "rgba(8fb4e6ee)", "rgba(6ac8dcee)" }, angle = 45 },
      inactive_border = "rgba(33364aaa)",
    },
    layout = "dwindle",
  },
  decoration = {
    rounding = 10,
    rounding_power = 2,
    dim_inactive = true,
    dim_strength = 0.08,
    shadow = { enabled = true, range = 10, render_power = 3, color = 0x99000000 },
    blur = { enabled = true, size = 4, passes = 2, vibrancy = 0.17 },
  },
  animations = { enabled = true },
  dwindle = { preserve_split = true },
  misc = {
    force_default_wallpaper = 0,
    disable_hyprland_logo = true,
    disable_splash_rendering = true,
    focus_on_activate = true,
  },
  input = {
    kb_layout = "us",
    follow_mouse = 1,
    repeat_rate = 30,
    repeat_delay = 600,
    sensitivity = 0,
    touchpad = { natural_scroll = true },
  },
})

-- window border colours follow the wallpaper (written by drivewood-palette)
pcall(dofile, home .. "/.local/state/drivewood/border.lua")
-- choices made in Drivewood Settings (keyboard, mouse, screens, gaps, corners...)
pcall(dofile, home .. "/.config/hypr/drivewood-settings.lua")
-- mouse turned off with Super + M (cleared at the next login)
pcall(dofile, (os.getenv("XDG_RUNTIME_DIR") or "/tmp") .. "/drivewood-mouse-off.lua")

-- motion: windows float in gently, workspaces glide
hl.curve("drift", { type = "bezier", points = { { 0.22, 1 }, { 0.36, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.animation({ leaf = "global", enabled = true, speed = 8, bezier = "drift" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 5, bezier = "drift", style = "popin 80%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 2, bezier = "linear", style = "popin 85%" })
hl.animation({ leaf = "fade", enabled = true, speed = 4, bezier = "drift" })
hl.animation({ leaf = "layers", enabled = true, speed = 4, bezier = "drift", style = "fade" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 4, bezier = "drift", style = "slidefade 15%" })

hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

-- ---- keys ------------------------------------------------------------------
local M = "SUPER"
-- tap Super on its own: the Drivewood menu (cancelled if another key is pressed meanwhile)
for _, key in ipairs({ "Super_L", "Super_R" }) do
  hl.bind(M .. " + " .. key, hl.dsp.exec_cmd(shell .. "menu"), { release = true, description = "Drivewood menu" })
end
hl.bind(M .. " + ALT + SPACE", hl.dsp.exec_cmd(shell .. "apps"), { description = "All apps" })
hl.bind(M .. " + RETURN", hl.dsp.exec_cmd("foot"), { description = "Terminal" })
-- Alt + Tab: switch between open apps (hold Alt and press Tab again to go further back)
hl.bind("ALT + TAB", hl.dsp.exec_cmd(shell .. "switchNext"), { description = "Switch app" })
hl.bind("ALT + SHIFT + TAB", hl.dsp.exec_cmd(shell .. "switchPrev"), { description = "Switch app (back)" })
-- letting go of Alt picks the highlighted app (also when Shift is still held)
for _, key in ipairs({ "Alt_L", "Alt_R" }) do
  hl.bind("ALT + " .. key, hl.dsp.exec_cmd(shell .. "switchDone"), { release = true })
  hl.bind("ALT + SHIFT + " .. key, hl.dsp.exec_cmd(shell .. "switchDone"), { release = true })
end
-- Super + Tab: next workspace (1 to 5, wraps around, empty ones too); add Shift to go back
hl.bind(M .. " + TAB", hl.dsp.exec_cmd("drivewood-workspace next"), { description = "Next workspace" })
hl.bind(M .. " + SHIFT + TAB", hl.dsp.exec_cmd("drivewood-workspace prev"), { description = "Previous workspace" })
-- Super + M: turn the mouse off / on (hides it and ignores it)
hl.bind(M .. " + M", hl.dsp.exec_cmd("drivewood-mouse"), { description = "Mouse off / on" })
hl.bind(M .. " + B", hl.dsp.exec_cmd("zen-browser"), { description = "Browser" })
hl.bind(M .. " + E", hl.dsp.exec_cmd("nautilus --new-window"), { description = "Files" })
hl.bind(M .. " + ALT + L", hl.dsp.exec_cmd("drivewood-link"), { description = "DriveWood Link" })
hl.bind(M .. " + ALT + D", hl.dsp.exec_cmd("drivewood-landscape"), { description = "Landscape" })
hl.bind(M .. " + ALT + T", hl.dsp.exec_cmd("drivewood-tidepool"), { description = "Tidepool" })
hl.bind(M .. " + I", hl.dsp.exec_cmd("drivewood-settings"), { description = "Settings" })
hl.bind(M .. " + L", hl.dsp.exec_cmd("loginctl lock-session"), { description = "Lock" })
hl.bind(M .. " + W", hl.dsp.window.close(), { description = "Close window" })
hl.bind(M .. " + Q", hl.dsp.window.close(), { description = "Close window (also)" })
hl.bind(M .. " + V", hl.dsp.window.float({ action = "toggle" }), { description = "Float window" })
hl.bind(M .. " + F", hl.dsp.window.fullscreen(), { description = "Full screen" })
hl.bind(M .. " + J", hl.dsp.layout("togglesplit"), { description = "Flip split" })
hl.bind("PRINT", hl.dsp.exec_cmd("drivewood-screenshot area"), { description = "Screenshot of an area" })
hl.bind("SHIFT + PRINT", hl.dsp.exec_cmd("drivewood-screenshot screen"), { description = "Screenshot of the screen" })

for _, d in ipairs({ "left", "right", "up", "down" }) do
  hl.bind(M .. " + " .. d, hl.dsp.focus({ direction = d }), { description = "Focus " .. d })
end
for i = 1, 10 do
  local key = i % 10
  hl.bind(M .. " + " .. key, hl.dsp.focus({ workspace = i }), { description = "Workspace " .. i })
  hl.bind(M .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }), { description = "Move to workspace " .. i })
end
hl.bind(M .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(M .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
hl.bind(M .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(M .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), { locked = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), { locked = true })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { locked = true, repeating = true })
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })

-- ---- windows -----------------------------------------------------------------
hl.window_rule({ name = "suppress-maximize", match = { class = ".*" }, suppress_event = "maximize" })
-- DriveWood Link: a small floating window, never full screen
hl.window_rule({ name = "link-main", match = { class = "^org.drivewood.Link$", title = "^DriveWood Link$" }, float = true, center = true, size = { 540, 600 } })
hl.window_rule({ name = "link-docs", match = { class = "^org.drivewood.Link$", title = "^(Terms of Use|Privacy Policy|Text to .*)$" }, float = true, center = true, size = { 600, 640 } })
hl.window_rule({ name = "link-control", match = { class = "^org.drivewood.Link$", title = "^Controlling .*$" }, float = true, center = true, size = { 1120, 720 } })
hl.window_rule({ name = "link-banner", match = { class = "^org.drivewood.Link$", title = "^DriveWood Link remote control$" }, float = true, pin = true, size = { 420, 56 } })
-- Drivewood Settings
hl.window_rule({ name = "settings", match = { class = "^org.drivewood.Settings$" }, float = true, center = true, size = { 900, 640 } })
-- small tools float
hl.window_rule({ name = "tools", match = { class = "^(pavucontrol|nm-connection-editor|blueman-manager|org.gnome.Nautilus)$", title = "^(Properties|.*Preferences.*)$" }, float = true, center = true })

-- ---- start -------------------------------------------------------------------
hl.on("hyprland.start", function()
  hl.exec_cmd("drivewood-wallpaper restore")
  hl.exec_cmd("drivewood-sky --force")
  hl.exec_cmd("qs -n -p /usr/share/drivewood/shell")
  hl.exec_cmd("mako")
  hl.exec_cmd("gsettings set org.gnome.desktop.interface color-scheme prefer-dark")
  hl.exec_cmd("gsettings set org.gnome.desktop.interface icon-theme Papirus-Dark")
  hl.exec_cmd("hypridle")
  hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE")
  hl.exec_cmd("systemctl --user start drivewood-sky.timer drivewood-link.service")
  -- the lock screen doubles as the sign-in screen after boot
  hl.exec_cmd("hyprlock")
end)

pcall(dofile, home .. "/.config/hypr/custom.lua")

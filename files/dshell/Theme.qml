pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Driftwood palette, shared helpers and the time of day.
Singleton {
  id: theme

  // Desktop entries load lazily: touch them at startup and count changes, so
  // anything bound to appsSerial refreshes once the list has filled in.
  property int appsSerial: 0
  Component.onCompleted: DesktopEntries.applications.values
  Connections {
    target: DesktopEntries.applications
    function onValuesChanged() { theme.appsSerial++ }
  }

  // apps the system marks as hidden (the same list Omarchy's launcher uses)
  property var hidden: ({})
  Process {
    running: true
    command: ["bash", "-c", "\"${OMARCHY_PATH:-/usr/share/omarchy}/shell/services/hidden-entries.sh\" \"${XDG_CURRENT_DESKTOP:-Hyprland}\""]
    stdout: StdioCollector {
      onStreamFinished: {
        var map = {}
        text.split("\n").forEach(function(line) {
          var id = line.trim().replace(/\.desktop$/, "")
          if (id) map[id] = true
        })
        theme.hidden = map
        theme.appsSerial++
      }
    }
  }

  // ---- colours that follow the wallpaper (see driftwood-palette) ----
  property color accent: "#8fb4e6"
  property color accent2: "#6ac8dc"
  property color bg: "#0f1118"

  function a(c, alpha) { return Qt.rgba(c.r, c.g, c.b, alpha) }

  function applyPalette(raw) {
    try {
      var p = JSON.parse(raw)
      if (p.accent) theme.accent = p.accent
      if (p.accent2) theme.accent2 = p.accent2
      if (p.bg) theme.bg = p.bg
    } catch (e) {}
  }

  FileView {
    path: Quickshell.env("HOME") + "/.local/state/driftwood/palette.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: theme.applyPalette(text())
  }

  // whenever the wallpaper changes (timer, menu, picker), rebuild the palette
  property string lastBackground: ""
  Process {
    id: bgRead
    command: ["readlink", "-f", Quickshell.env("HOME") + "/.local/state/omarchy/current/background"]
    stdout: StdioCollector {
      onStreamFinished: {
        var p = text.trim()
        if (p && p !== theme.lastBackground) {
          theme.lastBackground = p
          paletteRun.command = [Quickshell.env("HOME") + "/.local/bin/driftwood-palette", p]
          paletteRun.running = true
        }
      }
    }
  }
  Process { id: paletteRun }
  Timer { interval: 2500; running: true; repeat: true; triggeredOnStart: true; onTriggered: bgRead.running = true }

  readonly property color bg2: "#171a24"
  readonly property color bg3: "#20243200"
  readonly property color line: "#2b3040"
  readonly property color fg: "#e6dccb"
  readonly property color bright: "#f4ecdd"
  readonly property color dim: "#7d7f8f"
  readonly property color peach: "#f2a97a"
  readonly property color violet: "#c79ad6"
  readonly property color teal: "#86c4c0"
  readonly property color pine: "#9fc48a"
  readonly property color sky: "#7f9fd9"
  readonly property color red: "#e8746a"
  readonly property string font: "JetBrainsMono Nerd Font"
  readonly property string user: Quickshell.env("USER") || "friend"
  readonly property string home: Quickshell.env("HOME")

  function run(command) {
    Quickshell.execDetached(["bash", "-lc", command])
  }

  function quote(value) {
    return "'" + String(value).replace(/'/g, "'\\''") + "'"
  }

  // ---- time of day: dawn 05-08, day 08-17, dusk 17-20, night ----
  property date now: new Date()
  Timer {
    interval: 30000; running: true; repeat: true
    onTriggered: theme.now = new Date()
  }
  readonly property int hour: now.getHours()
  readonly property string phase: hour >= 5 && hour < 8 ? "dawn"
                                : hour >= 8 && hour < 17 ? "day"
                                : hour >= 17 && hour < 20 ? "dusk" : "night"
  readonly property string skyIcon: phase === "dawn" ? "\u{F059C}"
                                  : phase === "day" ? "\u{F0599}"
                                  : phase === "dusk" ? "\u{F059B}" : "\u{F0594}"
  readonly property color skyColor: accent
  // the horizon line under the bar takes the wallpaper's colours
  readonly property color horizonA: accent
  readonly property color horizonB: accent2
  readonly property string greeting: phase === "dawn" ? "Early light"
                                   : phase === "day" ? (hour < 12 ? "Good morning" : "Good afternoon")
                                   : phase === "dusk" ? "Good evening" : "Quiet night"

  // ---- apps ----
  // background helpers that are not apps you'd open yourself
  readonly property var helperNames: ["Foot Client", "Foot Server", "Fcitx 5 Configuration", "Fcitx 5"]

  function iconFor(entry) {
    var icon = String((entry && entry.icon) || "")
    if (icon.charAt(0) === "/") return "file://" + icon
    var themed = icon.length ? Quickshell.iconPath(icon, true) : ""
    return themed.length ? themed : Quickshell.iconPath("application-x-executable", true)
  }

  function launchEntry(entry) {
    if (!entry) return
    if (entry.runInTerminal) {
      var words = (entry.command || []).filter(function(w) { return !/^%[a-zA-Z]$/.test(String(w)) })
      run("omarchy-launch-tui " + words.map(quote).join(" "))
    } else {
      run("uwsm-app -- gtk-launch " + quote(entry.id + ".desktop"))
    }
  }

  function apps() {
    var list = (DesktopEntries.applications.values || []).filter(function(e) {
      return e && !e.noDisplay && !theme.hidden[String(e.id).replace(/\.desktop$/, "")]
        && theme.helperNames.indexOf(String(e.name)) === -1
    })
    list.sort(function(a, b) { return String(a.name).toLowerCase().localeCompare(String(b.name).toLowerCase()) })
    return list
  }

  function matches(entry, query) {
    var q = String(query || "").toLowerCase()
    if (!q) return true
    var hay = [entry.name, entry.genericName, entry.comment, entry.id].join(" ").toLowerCase()
    return hay.indexOf(q) !== -1
  }
}

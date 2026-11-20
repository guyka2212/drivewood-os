import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

// Switcher: Alt + Tab. Each press jumps straight to the next window (most recently used first),
// so a quick Alt + Tab flips between your last two apps. Keep holding Alt and press Tab again to
// walk further; Shift goes back. A strip of the open apps shows which one you're on and goes away
// as soon as you let go of Alt.
PanelWindow {
  id: sw

  property bool opened: false
  property var wins: []      // snapshot for this Alt press: [{ address, title, cls }]
  property int sel: 0
  property int pending: 0    // presses that came in before the window list arrived
  property int focused: -1   // the window we already jumped to
  property bool letGo: false // Alt was let go before the window list arrived

  visible: opened
  anchors { top: true; bottom: true; left: true; right: true }
  color: "transparent"
  exclusionMode: ExclusionMode.Ignore
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.namespace: "drivewood-switcher"
  // keyboard focus only so we notice Alt being let go
  WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

  function step(dir) {
    endTimer.restart()
    if (opened || listing.running) {
      if (listing.running) { pending += dir; return }
      move(dir)
      return
    }
    pending = dir
    letGo = false
    listing.running = true
  }

  // The first jump happens at once (before the strip takes the keyboard), so a quick Alt + Tab
  // is instant. While the strip is up Hyprland keeps focus where it is, so later presses only move
  // the highlight and the chosen window gets focus when Alt is let go.
  function move(dir) {
    if (wins.length < 2) return
    sel = (sel + dir + wins.length) % wins.length
    if (focused < 0) { focused = sel; focusWin(wins[sel]) }
  }

  function focusWin(w) {
    if (!w) return
    Quickshell.execDetached(["hyprctl", "dispatch", 'hl.dsp.focus({ window = "address:' + w.address + '" })'])
  }

  function done() {
    if (listing.running) { letGo = true; return }
    if (!opened) return
    // refocus where you started first, so the next quick Alt + Tab goes back there
    if (sel !== focused && wins[sel]) { later.start_ = wins[0]; later.target = wins[sel]; later.restart() }
    opened = false; wins = []; sel = 0; pending = 0; focused = -1; endTimer.stop()
  }
  // focus the chosen window once the strip has let go of the keyboard
  Timer {
    id: later
    property var start_: null
    property var target: null
    interval: 120
    onTriggered: {
      var f = function(w) { return "hyprctl dispatch " + Theme.quote('hl.dsp.focus({ window = "address:' + w.address + '" })') }
      Quickshell.execDetached(["sh", "-c", f(start_) + "; " + f(target)])
    }
  }

  Process {
    id: listing
    command: ["hyprctl", "clients", "-j"]
    stdout: StdioCollector {
      onStreamFinished: {
        var list = []
        try { list = JSON.parse(text) } catch (e) { list = [] }
        list = list.filter(function(c) { return c.mapped && !c.hidden && c.workspace && c.workspace.id > 0 })
        list.sort(function(a, b) { return a.focusHistoryID - b.focusHistoryID })
        sw.wins = list.map(function(c) { return { address: c.address, title: c.title || c.class, cls: c.class || "" } })
        sw.sel = 0
        if (sw.wins.length < 2) { sw.wins = []; return }
        var p = sw.pending; sw.pending = 0
        if (sw.letGo) {  // a quick tap that was already over: just jump, no strip
          sw.letGo = false
          sw.focusWin(sw.wins[((p === 0 ? 1 : p) % sw.wins.length + sw.wins.length) % sw.wins.length])
          sw.wins = []
          return
        }
        sw.opened = true
        sw.move(p === 0 ? 1 : p)
        Qt.callLater(function() { keys.forceActiveFocus() })
      }
    }
  }

  // safety net in case the Alt release is missed
  Timer { id: endTimer; interval: 2500; onTriggered: sw.done() }

  function entryFor(cls) {
    if (!cls) return null
    if (typeof DesktopEntries.heuristicLookup === "function") return DesktopEntries.heuristicLookup(cls)
    return DesktopEntries.byId(cls)
  }

  Item {
    id: keys
    anchors.fill: parent
    focus: true
    Keys.onReleased: function(e) { if (e.key === Qt.Key_Alt || e.key === Qt.Key_Meta) sw.done() }
    Keys.onPressed: function(e) {
      if (e.key === Qt.Key_Escape) { sw.sel = 0; sw.done(); e.accepted = true }  // back to where you were
      else if (e.key === Qt.Key_Tab || e.key === Qt.Key_Right) { sw.step(1); e.accepted = true }
      else if (e.key === Qt.Key_Backtab || e.key === Qt.Key_Left) { sw.step(-1); e.accepted = true }
      else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) { sw.done(); e.accepted = true }
    }
  }

  MouseArea { anchors.fill: parent; onClicked: sw.done() }

  Rectangle {
    id: strip
    anchors.centerIn: parent
    width: Math.min(row.implicitWidth + 32, sw.width - 64)
    height: 168
    radius: 18
    color: Theme.a(Theme.bg, 0.92)
    border { color: Theme.line; width: 1 }
    clip: true
    opacity: sw.opened ? 1 : 0
    scale: sw.opened ? 1 : 0.96
    Behavior on opacity { NumberAnimation { duration: 120 } }
    Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

    ListView {
      id: row
      anchors { fill: parent; margins: 16 }
      orientation: ListView.Horizontal
      spacing: 10
      implicitWidth: sw.wins.length * 132 - 10
      model: sw.wins
      currentIndex: sw.sel
      highlightMoveDuration: 120
      delegate: Rectangle {
        required property var modelData
        required property int index
        width: 122; height: 136
        radius: 12
        color: index === sw.sel ? Theme.a(Theme.accent, 0.22) : "transparent"
        border { color: index === sw.sel ? Theme.accent : "transparent"; width: 2 }
        Image {
          anchors { top: parent.top; topMargin: 14; horizontalCenter: parent.horizontalCenter }
          width: 64; height: 64
          sourceSize { width: 64; height: 64 }
          smooth: true
          source: Theme.iconFor(sw.entryFor(modelData.cls))
        }
        Text {
          anchors { bottom: parent.bottom; bottomMargin: 12; left: parent.left; right: parent.right; margins: 8 }
          horizontalAlignment: Text.AlignHCenter
          elide: Text.ElideRight
          maximumLineCount: 2
          wrapMode: Text.Wrap
          text: modelData.title
          font { family: Theme.font; pixelSize: 11 }
          color: index === sw.sel ? Theme.bright : Theme.dim
        }
        MouseArea {
          anchors.fill: parent
          onClicked: { sw.sel = index; sw.done() }
        }
      }
    }
  }
}

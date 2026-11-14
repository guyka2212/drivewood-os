import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Services.Pipewire

// Driftline: a floating pill with a time-of-day horizon line along its bottom.
PanelWindow {
  id: bar
  signal menuRequested()
  signal appsRequested()

  anchors { top: true; left: true; right: true }
  margins { top: 8; left: 10; right: 10 }
  implicitHeight: 38
  exclusiveZone: 42
  color: "transparent"
  WlrLayershell.namespace: "drivewood-bar"

  readonly property var monitor: Hyprland.monitorFor(bar.screen)
  readonly property string monitorName: monitor ? monitor.name : ""
  readonly property int activeId: monitor && monitor.activeWorkspace ? monitor.activeWorkspace.id : 1
  readonly property int block: Math.floor((activeId - 1) / 10)

  // ---------------- live system stats ----------------
  property real cpu: 0
  property real mem: 0
  property var lastCpu: null
  Process {
    id: statProc
    command: ["bash", "-c", "head -1 /proc/stat; grep -E '^(MemTotal|MemAvailable):' /proc/meminfo"]
    stdout: StdioCollector {
      onStreamFinished: {
        var lines = text.split("\n")
        var f = lines[0].trim().split(/\s+/).slice(1).map(Number)
        var idle = f[3] + (f[4] || 0), total = f.reduce(function(a, b) { return a + b }, 0)
        if (bar.lastCpu) {
          var dt = total - bar.lastCpu.total, di = idle - bar.lastCpu.idle
          if (dt > 0) bar.cpu = Math.max(0, Math.min(1, 1 - di / dt))
        }
        bar.lastCpu = { total: total, idle: idle }
        var memTotal = parseInt((lines[1] || "").replace(/\D+/g, "")) || 1
        var memAvail = parseInt((lines[2] || "").replace(/\D+/g, "")) || 0
        bar.mem = 1 - memAvail / memTotal
      }
    }
  }
  Timer { interval: 2000; running: true; repeat: true; triggeredOnStart: true; onTriggered: statProc.running = true }

  PwObjectTracker { objects: [Pipewire.defaultAudioSink] }
  readonly property var sink: Pipewire.defaultAudioSink
  readonly property real volume: sink && sink.audio ? sink.audio.volume : 0
  readonly property bool muted: sink && sink.audio ? sink.audio.muted : false

  SystemClock { id: clock; precision: SystemClock.Minutes }

  // ---------------- the pill ----------------
  Rectangle {
    id: pill
    anchors.fill: parent
    radius: 13
    color: Theme.a(Theme.bg, 0.86)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.06)
    clip: true

    // horizon line: changes with the time of day
    Rectangle {
      anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 14; rightMargin: 14 }
      height: 2
      radius: 1
      opacity: 0.9
      gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: 0.0; color: "transparent" }
        GradientStop { position: 0.25; color: Theme.horizonA }
        GradientStop { position: 0.75; color: Theme.horizonB }
        GradientStop { position: 1.0; color: "transparent" }
      }
    }

    // ---- left: pine, stones, window title ----
    RowLayout {
      anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: 8 }
      spacing: 10

      Rectangle {
        id: pine
        Layout.preferredWidth: 28; Layout.preferredHeight: 26
        radius: 8
        color: pineMouse.containsMouse ? Theme.a(Theme.accent, 0.18) : "transparent"
        Behavior on color { ColorAnimation { duration: 150 } }
        Text {
          anchors.centerIn: parent
          text: ""
          font { family: Theme.font; pixelSize: 15 }
          color: Theme.pine
        }
        MouseArea {
          id: pineMouse
          anchors.fill: parent
          hoverEnabled: true
          acceptedButtons: Qt.LeftButton | Qt.RightButton
          cursorShape: Qt.PointingHandCursor
          onClicked: function(m) { if (m.button === Qt.RightButton) bar.appsRequested(); else bar.menuRequested() }
        }
      }

      Row {
        spacing: 6
        Repeater {
          model: 5
          delegate: Rectangle {
            required property int index
            readonly property int wsId: bar.block * 10 + index + 1
            readonly property bool active: wsId === bar.activeId
            readonly property bool occupied: {
              var ws = Hyprland.workspaces.values
              for (var i = 0; i < ws.length; i++) if (ws[i].id === wsId) return true
              return false
            }
            anchors.verticalCenter: parent.verticalCenter
            width: active ? 24 : 10
            height: 10
            radius: 5
            color: active ? Theme.accent : occupied ? Qt.rgba(0.9, 0.86, 0.8, 0.55) : "transparent"
            border.width: active || occupied ? 0 : 1
            border.color: Qt.rgba(0.9, 0.86, 0.8, 0.35)
            Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
            Behavior on color { ColorAnimation { duration: 220 } }
            MouseArea {
              anchors.fill: parent
              anchors.margins: -4
              cursorShape: Qt.PointingHandCursor
              onClicked: Theme.run("drivewood-workspace " + (index + 1))
            }
          }
        }
      }

      Text {
        Layout.maximumWidth: 260
        Layout.leftMargin: 6
        text: ToplevelManager.activeToplevel ? (ToplevelManager.activeToplevel.title || "") : ""
        elide: Text.ElideRight
        font { family: Theme.font; pixelSize: 12 }
        color: Theme.dim
      }
    }

    // ---- centre: sky, time, date ----
    Row {
      anchors.centerIn: parent
      spacing: 9
      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: Theme.skyIcon
        font { family: Theme.font; pixelSize: 16 }
        color: Theme.skyColor
      }
      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: Qt.formatDateTime(clock.date, "HH:mm")
        font { family: Theme.font; pixelSize: 15; bold: true }
        color: Theme.bright
      }
      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: Qt.formatDateTime(clock.date, "ddd d MMM")
        font { family: Theme.font; pixelSize: 12 }
        color: Theme.dim
      }
    }

    // ---- right: cpu, memory, volume, power ----
    Row {
      anchors { right: parent.right; verticalCenter: parent.verticalCenter; rightMargin: 10 }
      spacing: 14

      // update available: a small down arrow next to the usage bars (drivewood-update-check writes the file)
      Item {
        id: updateArrow
        property bool available: false
        property string version: ""
        visible: available
        width: visible ? 22 : 0
        height: 22
        anchors.verticalCenter: parent.verticalCenter
        FileView {
          path: Quickshell.env("HOME") + "/.local/state/drivewood/update.json"
          watchChanges: true
          printErrors: false
          onFileChanged: reload()
          onLoaded: {
            try {
              var u = JSON.parse(text())
              updateArrow.available = !!u.available
              updateArrow.version = u.version || ""
            } catch (e) { updateArrow.available = false }
          }
          onLoadFailed: updateArrow.available = false
        }
        Rectangle {
          anchors.fill: parent
          radius: 11
          color: arrowMouse.containsMouse ? Theme.a(Theme.accent, 0.25) : Theme.a(Theme.accent, 0.12)
        }
        Text {
          anchors.centerIn: parent
          text: "\u{F01DA}"
          color: Theme.accent
          font { family: Theme.font; pixelSize: 14 }
          SequentialAnimation on y {
            running: updateArrow.visible
            loops: Animation.Infinite
            NumberAnimation { from: 2; to: 5; duration: 700; easing.type: Easing.InOutSine }
            NumberAnimation { from: 5; to: 2; duration: 700; easing.type: Easing.InOutSine }
          }
        }
        MouseArea {
          id: arrowMouse
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onClicked: Theme.run("drivewood-update")
        }
      }

      Repeater {
        model: [
          { icon: "", label: "cpu", tint: Theme.accent2 },
          { icon: "", label: "mem", tint: Theme.accent2 }
        ]
        delegate: Row {
          required property var modelData
          readonly property real value: modelData.label === "cpu" ? bar.cpu : bar.mem
          spacing: 6
          anchors.verticalCenter: parent.verticalCenter
          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: modelData.icon
            font { family: Theme.font; pixelSize: 13 }
            color: modelData.tint
          }
          Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 34; height: 5; radius: 3
            color: Qt.rgba(1, 1, 1, 0.08)
            Rectangle {
              width: Math.max(4, parent.width * value); height: parent.height; radius: 3
              color: modelData.tint
              Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
            }
          }
          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: Math.round(value * 100) + "%"
            font { family: Theme.font; pixelSize: 11 }
            color: Theme.dim
            width: 30
          }
        }
      }

      Item {
        width: volRow.width; height: 26
        anchors.verticalCenter: parent.verticalCenter
        Row {
          id: volRow
          spacing: 6
          anchors.verticalCenter: parent.verticalCenter
          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: bar.muted ? "\u{F075F}" : bar.volume > 0.5 ? "\u{F057E}" : "\u{F0580}"
            font { family: Theme.font; pixelSize: 15 }
            color: bar.muted ? Theme.red : Theme.accent
          }
          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: Math.round(bar.volume * 100) + "%"
            font { family: Theme.font; pixelSize: 11 }
            color: Theme.dim
          }
        }
        MouseArea {
          anchors.fill: parent
          cursorShape: Qt.PointingHandCursor
          onClicked: if (bar.sink && bar.sink.audio) bar.sink.audio.muted = !bar.sink.audio.muted
          onWheel: function(w) {
            if (!bar.sink || !bar.sink.audio) return
            bar.sink.audio.volume = Math.max(0, Math.min(1.5, bar.sink.audio.volume + (w.angleDelta.y > 0 ? 0.05 : -0.05)))
          }
        }
      }

      Rectangle {
        width: 26; height: 26; radius: 8
        anchors.verticalCenter: parent.verticalCenter
        color: powerMouse.containsMouse ? Qt.rgba(0.91, 0.45, 0.42, 0.2) : "transparent"
        Behavior on color { ColorAnimation { duration: 150 } }
        Text {
          anchors.centerIn: parent
          text: "⏻"
          font { family: Theme.font; pixelSize: 14 }
          color: powerMouse.containsMouse ? Theme.red : Theme.fg
        }
        MouseArea {
          id: powerMouse
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onClicked: bar.menuRequested()
        }
      }
    }
  }
}

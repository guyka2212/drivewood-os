import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland

// Tide: the Super menu. Greeting, search across apps and actions, favourites,
// quick actions and power. Fully keyboard driven: arrows, Tab, Enter, Esc.
PanelWindow {
  id: tide
  signal appsRequested()

  property bool opened: false
  property string query: ""
  property int sel: 0

  visible: opened
  anchors { top: true; bottom: true; left: true; right: true }
  color: "transparent"
  exclusionMode: ExclusionMode.Ignore
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.namespace: "driftwood-tide"
  WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

  readonly property string home: Theme.home
  readonly property var favs: [
    { icon: "", label: "Terminal", tint: Theme.pine, cmd: "xdg-terminal-exec" },
    { icon: "", label: "Browser", tint: Theme.accent, cmd: "omarchy-launch-browser" },
    { icon: "", label: "Files", tint: Theme.accent, cmd: "uwsm-app -- nautilus --new-window" },
    { icon: "", label: "Landscape", tint: Theme.accent2, cmd: "xdg-terminal-exec " + home + "/driftwood/driftwood.py" },
    { icon: "󰌷", label: "Link", tint: Theme.accent2, cmd: "drivewood-link" },
    { icon: "", label: "Studio", tint: Theme.pine, cmd: "uwsm-app -- gtk-launch android-studio.desktop" },
    { icon: "", label: "Apps", tint: Theme.bright, action: "apps" }
  ]
  readonly property var quick: [
    { icon: "", label: "Next wallpaper", hint: "drift to the next sky", cmd: "omarchy-theme-bg-next" },
    { icon: "", label: "Sky to clock", hint: "match the real time of day", cmd: home + "/.local/bin/driftwood-sky --force" },
    { icon: "", label: "All settings", hint: "the full system menu", cmd: "all-settings" }
  ]
  readonly property var power: [
    { icon: "", label: "Lock", tint: Theme.accent, cmd: "omarchy-system-lock" },
    { icon: "", label: "Restart", tint: Theme.accent, cmd: "systemctl reboot" },
    { icon: "⏻", label: "Shut down", tint: Theme.red, cmd: "systemctl poweroff" }
  ]

  // with a query: matching actions first, then matching apps
  readonly property var results: {
    if (!query) return []
    var serial = Theme.appsSerial
    var q = query.toLowerCase(), out = []
    favs.concat(quick).concat(power).forEach(function(item) {
      if (item.label.toLowerCase().indexOf(q) !== -1) out.push(item)
    })
    Theme.apps().forEach(function(e) {
      if (out.length < 9 && Theme.matches(e, q)) out.push({ label: e.name, hint: e.genericName || e.comment || "", entry: e })
    })
    return out
  }
  readonly property var flat: query ? results : favs.concat(quick).concat(power)

  function open() { query = ""; sel = 0; opened = true; Qt.callLater(function() { input.forceActiveFocus() }) }
  function close() { opened = false }
  function toggle() { opened ? close() : open() }

  function activate(item) {
    if (!item) return
    close()
    if (item.action === "apps") appsRequested()
    else if (item.entry) Theme.launchEntry(item.entry)
    else Theme.run(item.cmd)
  }

  function move(step) {
    if (flat.length === 0) return
    sel = (sel + step + flat.length) % flat.length
  }

  onQueryChanged: sel = 0

  // ---- dusk wash; click outside to close ----
  Rectangle {
    anchors.fill: parent
    gradient: Gradient {
      GradientStop { position: 0.0; color: Qt.rgba(0.04, 0.05, 0.09, 0.55) }
      GradientStop { position: 1.0; color: Theme.a(Qt.lighter(Theme.bg, 1.9), 0.62) }
    }
    MouseArea { anchors.fill: parent; onClicked: tide.close() }
  }

  // ---- the card ----
  Rectangle {
    id: card
    width: 600
    height: body.implicitHeight + 40
    x: (parent.width - width) / 2
    y: parent.height * 0.14
    radius: 20
    color: Theme.a(Theme.bg, 0.94)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.07)
    opacity: tide.opened ? 1 : 0
    scale: tide.opened ? 1 : 0.96
    Behavior on opacity { NumberAnimation { duration: 160 } }
    Behavior on scale { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
    MouseArea { anchors.fill: parent }   // swallow clicks on the card

    // sunrise-to-dusk accent along the top edge
    Rectangle {
      anchors { top: parent.top; left: parent.left; right: parent.right; leftMargin: 24; rightMargin: 24 }
      height: 2
      gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: 0.0; color: "transparent" }
        GradientStop { position: 0.2; color: Theme.accent }
        GradientStop { position: 0.8; color: Theme.accent2 }
        GradientStop { position: 1.0; color: "transparent" }
      }
    }

    ColumnLayout {
      id: body
      anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
      spacing: 16

      // greeting
      RowLayout {
        Layout.fillWidth: true
        spacing: 12
        Text {
          text: Theme.skyIcon
          font { family: Theme.font; pixelSize: 26 }
          color: Theme.skyColor
        }
        ColumnLayout {
          spacing: 0
          Text {
            text: Theme.greeting + ", " + Theme.user
            font { family: Theme.font; pixelSize: 19; bold: true }
            color: Theme.bright
          }
          Text {
            text: Qt.formatDateTime(Theme.now, "dddd, d MMMM")
            font { family: Theme.font; pixelSize: 12 }
            color: Theme.dim
          }
        }
        Item { Layout.fillWidth: true }
        Text {
          text: Qt.formatDateTime(Theme.now, "HH:mm")
          font { family: Theme.font; pixelSize: 26 }
          color: Theme.fg
        }
      }

      // search
      Rectangle {
        Layout.fillWidth: true
        height: 42
        radius: 12
        color: Qt.rgba(1, 1, 1, 0.045)
        border.width: 1
        border.color: input.activeFocus ? Theme.a(Theme.accent, 0.55) : Qt.rgba(1, 1, 1, 0.08)
        Text {
          id: searchIcon
          anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
          text: ""
          font { family: Theme.font; pixelSize: 14 }
          color: Theme.accent
        }
        TextInput {
          id: input
          anchors { left: searchIcon.right; right: parent.right; leftMargin: 12; rightMargin: 14; verticalCenter: parent.verticalCenter }
          font { family: Theme.font; pixelSize: 14 }
          color: Theme.bright
          selectionColor: Theme.accent
          text: tide.query
          onTextChanged: tide.query = text
          Text {
            visible: !input.text
            text: "Search apps and actions…"
            font: input.font
            color: Theme.dim
          }
          Keys.onPressed: function(e) {
            if (e.key === Qt.Key_Escape) { tide.close(); e.accepted = true }
            else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) { tide.activate(tide.flat[tide.sel]); e.accepted = true }
            else if (e.key === Qt.Key_Down || e.key === Qt.Key_Tab) { tide.move(tide.query ? 1 : (tide.sel < tide.favs.length ? tide.favs.length - tide.sel : 1)); e.accepted = true }
            else if (e.key === Qt.Key_Up || e.key === Qt.Key_Backtab) { tide.move(-1); e.accepted = true }
            else if (!input.text && e.key === Qt.Key_Right) { tide.move(1); e.accepted = true }
            else if (!input.text && e.key === Qt.Key_Left) { tide.move(-1); e.accepted = true }
          }
        }
      }

      // ---- browse view: favourites, quick actions, power ----
      ColumnLayout {
        visible: !tide.query
        Layout.fillWidth: true
        spacing: 14

        RowLayout {
          Layout.fillWidth: true
          spacing: 10
          Repeater {
            model: tide.favs
            delegate: Rectangle {
              required property var modelData
              required property int index
              readonly property bool hot: tide.sel === index
              Layout.fillWidth: true
              height: 78
              radius: 14
              color: hot ? Theme.a(Theme.accent, 0.14) : Qt.rgba(1, 1, 1, 0.035)
              border.width: hot ? 1 : 0
              border.color: Theme.a(Theme.accent, 0.7)
              Behavior on color { ColorAnimation { duration: 120 } }
              Column {
                anchors.centerIn: parent
                spacing: 7
                Text {
                  anchors.horizontalCenter: parent.horizontalCenter
                  text: modelData.icon
                  font { family: Theme.font; pixelSize: 22 }
                  color: modelData.tint
                  scale: hot ? 1.12 : 1
                  Behavior on scale { NumberAnimation { duration: 160; easing.type: Easing.OutBack } }
                }
                Text {
                  anchors.horizontalCenter: parent.horizontalCenter
                  text: modelData.label
                  font { family: Theme.font; pixelSize: 11 }
                  color: hot ? Theme.bright : Theme.fg
                }
              }
              MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onEntered: tide.sel = index
                onClicked: tide.activate(modelData)
              }
            }
          }
        }

        Text {
          text: "QUICK"
          font { family: Theme.font; pixelSize: 10; letterSpacing: 2 }
          color: Theme.dim
        }

        Column {
          Layout.fillWidth: true
          spacing: 2
          Repeater {
            model: tide.quick
            delegate: Rectangle {
              required property var modelData
              required property int index
              readonly property int flatIndex: tide.favs.length + index
              readonly property bool hot: tide.sel === flatIndex
              width: parent.width
              height: 40
              radius: 10
              color: hot ? Theme.a(Theme.accent, 0.12) : "transparent"
              Behavior on color { ColorAnimation { duration: 120 } }
              Rectangle {
                visible: hot
                width: 3; height: 18; radius: 2
                anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                color: Theme.accent
              }
              Text {
                id: qIcon
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                text: modelData.icon
                width: 20
                font { family: Theme.font; pixelSize: 15 }
                color: hot ? Theme.accent : Theme.fg
              }
              Text {
                anchors { left: qIcon.right; leftMargin: 12; verticalCenter: parent.verticalCenter }
                text: modelData.label
                font { family: Theme.font; pixelSize: 13 }
                color: hot ? Theme.bright : Theme.fg
              }
              Text {
                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                text: modelData.hint
                font { family: Theme.font; pixelSize: 11 }
                color: Theme.dim
              }
              MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onEntered: tide.sel = flatIndex
                onClicked: tide.activate(modelData)
              }
            }
          }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1, 1, 1, 0.06) }

        RowLayout {
          Layout.fillWidth: true
          spacing: 8
          Repeater {
            model: tide.power
            delegate: Rectangle {
              required property var modelData
              required property int index
              readonly property int flatIndex: tide.favs.length + tide.quick.length + index
              readonly property bool hot: tide.sel === flatIndex
              implicitWidth: pRow.implicitWidth + 26
              height: 34
              radius: 17
              color: hot ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(1, 1, 1, 0.03)
              border.width: 1
              border.color: hot ? modelData.tint : Qt.rgba(1, 1, 1, 0.07)
              Row {
                id: pRow
                anchors.centerIn: parent
                spacing: 8
                Text {
                  text: modelData.label
                  font { family: Theme.font; pixelSize: 12 }
                  color: hot ? Theme.bright : Theme.fg
                }
              }
              MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onEntered: tide.sel = flatIndex
                onClicked: tide.activate(modelData)
              }
            }
          }
          Item { Layout.fillWidth: true }
          Text {
            text: "press Super to close"
            font { family: Theme.font; pixelSize: 10 }
            color: Theme.dim
            opacity: 0.7
          }
        }
      }

      // ---- search results ----
      Column {
        visible: !!tide.query
        Layout.fillWidth: true
        spacing: 2
        Repeater {
          model: tide.results
          delegate: Rectangle {
            required property var modelData
            required property int index
            readonly property bool hot: tide.sel === index
            width: parent.width
            height: 46
            radius: 10
            color: hot ? Theme.a(Theme.accent, 0.12) : "transparent"
            Item {
              id: rIcon
              width: 28; height: 28
              anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
              Image {
                visible: !!modelData.entry
                anchors.fill: parent
                source: modelData.entry ? Theme.iconFor(modelData.entry) : ""
                sourceSize: Qt.size(56, 56)
                fillMode: Image.PreserveAspectFit
              }
              Text {
                visible: !modelData.entry
                anchors.centerIn: parent
                text: modelData.icon || ""
                font { family: Theme.font; pixelSize: 16 }
                color: modelData.tint || Theme.accent
              }
            }
            Column {
              anchors { left: rIcon.right; leftMargin: 12; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
              Text {
                text: modelData.label
                font { family: Theme.font; pixelSize: 13 }
                color: hot ? Theme.bright : Theme.fg
              }
              Text {
                visible: !!modelData.hint
                width: parent.width
                elide: Text.ElideRight
                text: modelData.hint || ""
                font { family: Theme.font; pixelSize: 10 }
                color: Theme.dim
              }
            }
            MouseArea {
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: Qt.PointingHandCursor
              onEntered: tide.sel = index
              onClicked: tide.activate(modelData)
            }
          }
        }
        Text {
          visible: tide.results.length === 0
          text: "Nothing washed up for “" + tide.query + "”"
          font { family: Theme.font; pixelSize: 12 }
          color: Theme.dim
          topPadding: 8; bottomPadding: 8
        }
      }
    }
  }
}

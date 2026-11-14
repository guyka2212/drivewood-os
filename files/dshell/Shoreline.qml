import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland

// Shoreline: the Apps window. A dusk overlay with a horizon line, search,
// category chips and a grid whose tiles rise into place one after another.
PanelWindow {
  id: shore

  property bool opened: false
  property string query: ""
  property string category: "All"
  property int sel: 0
  property var shown: []

  visible: opened
  anchors { top: true; bottom: true; left: true; right: true }
  color: "transparent"
  exclusionMode: ExclusionMode.Ignore
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.namespace: "driftwood-shoreline"
  WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

  readonly property var chips: [
    { label: "All", cats: [] },
    { label: "Internet", cats: ["Network", "WebBrowser", "Email", "Chat"] },
    { label: "Office", cats: ["Office", "TextEditor", "Calendar"] },
    { label: "Media", cats: ["AudioVideo", "Audio", "Video", "Graphics", "Photography"] },
    { label: "Develop", cats: ["Development", "IDE"] },
    { label: "System", cats: ["System", "Settings", "Utility", "TerminalEmulator", "FileManager"] }
  ]

  function inCategory(entry) {
    if (category === "All") return true
    var cats = []
    for (var i = 0; i < chips.length; i++) if (chips[i].label === category) cats = chips[i].cats
    var own = entry.categories || []
    for (var j = 0; j < own.length; j++) if (cats.indexOf(String(own[j])) !== -1) return true
    return false
  }

  function refresh() {
    shown = Theme.apps().filter(function(e) { return inCategory(e) && Theme.matches(e, query) })
    sel = 0
  }

  function show() {
    query = ""; category = "All"
    refresh()
    opened = true
    Qt.callLater(function() { input.forceActiveFocus() })
  }
  function close() { opened = false }
  function toggle() { opened ? close() : show() }

  function launch(entry) {
    if (!entry) return
    close()
    Theme.launchEntry(entry)
  }

  function moveSel(step) {
    if (shown.length === 0) return
    sel = Math.max(0, Math.min(shown.length - 1, sel + step))
    grid.positionViewAtIndex(sel, GridView.Contain)
  }

  onQueryChanged: if (opened) refresh()
  onCategoryChanged: if (opened) refresh()
  Connections {
    target: Theme
    function onAppsSerialChanged() { if (shore.opened) shore.refresh() }
  }

  // ---- dusk wash with a horizon line and its reflection ----
  Rectangle {
    anchors.fill: parent
    opacity: shore.opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }
    gradient: Gradient {
      GradientStop { position: 0.0; color: Qt.rgba(0.04, 0.05, 0.09, 0.86) }
      GradientStop { position: 0.78; color: Theme.a(Qt.lighter(Theme.bg, 1.7), 0.90) }
      GradientStop { position: 1.0; color: Qt.rgba(0.05, 0.06, 0.11, 0.94) }
    }
    Rectangle {
      y: parent.height * 0.86
      width: parent.width; height: 2
      opacity: 0.8
      gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: 0.0; color: "transparent" }
        GradientStop { position: 0.3; color: Theme.horizonA }
        GradientStop { position: 0.7; color: Theme.horizonB }
        GradientStop { position: 1.0; color: "transparent" }
      }
    }
    Rectangle {
      y: parent.height * 0.86 + 6
      x: parent.width * 0.3
      width: parent.width * 0.4; height: 1
      opacity: 0.25
      color: Theme.horizonA
    }
    MouseArea { anchors.fill: parent; onClicked: shore.close() }
  }

  // ---- content ----
  ColumnLayout {
    id: content
    width: Math.floor(Math.min(1060, parent.width * 0.86) / 132) * 132
    x: (parent.width - width) / 2
    y: parent.height * 0.08
    height: parent.height * 0.74
    spacing: 18
    opacity: shore.opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 200 } }

    // header: title, count, search
    RowLayout {
      Layout.fillWidth: true
      spacing: 14
      Column {
        spacing: 2
        Text {
          text: "Apps"
          font { family: Theme.font; pixelSize: 28; bold: true }
          color: Theme.bright
        }
      }
      Text {
        Layout.alignment: Qt.AlignBottom
        bottomPadding: 6
        text: shore.shown.length + (shore.shown.length === 1 ? " app" : " apps")
        font { family: Theme.font; pixelSize: 12 }
        color: Theme.dim
      }
      Item { Layout.fillWidth: true }
      Rectangle {
        Layout.alignment: Qt.AlignBottom
        width: 340; height: 42; radius: 21
        color: Qt.rgba(1, 1, 1, 0.05)
        border.width: 1
        border.color: input.activeFocus ? Theme.a(Theme.accent, 0.6) : Qt.rgba(1, 1, 1, 0.08)
        Text {
          id: sIcon
          anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
          text: ""
          font { family: Theme.font; pixelSize: 14 }
          color: Theme.accent
        }
        TextInput {
          id: input
          anchors { left: sIcon.right; right: parent.right; leftMargin: 12; rightMargin: 16; verticalCenter: parent.verticalCenter }
          font { family: Theme.font; pixelSize: 14 }
          color: Theme.bright
          selectionColor: Theme.accent
          text: shore.query
          onTextChanged: shore.query = text
          Text {
            visible: !input.text
            text: "Search the shore…"
            font: input.font
            color: Theme.dim
          }
          Keys.onPressed: function(e) {
            var cols = Math.max(1, Math.floor(grid.width / grid.cellWidth))
            if (e.key === Qt.Key_Escape) { shore.close(); e.accepted = true }
            else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) { shore.launch(shore.shown[shore.sel]); e.accepted = true }
            else if (e.key === Qt.Key_Right) { shore.moveSel(1); e.accepted = true }
            else if (e.key === Qt.Key_Left) { shore.moveSel(-1); e.accepted = true }
            else if (e.key === Qt.Key_Down) { shore.moveSel(cols); e.accepted = true }
            else if (e.key === Qt.Key_Up) { shore.moveSel(-cols); e.accepted = true }
            else if (e.key === Qt.Key_Tab) {
              var i = 0
              for (var k = 0; k < shore.chips.length; k++) if (shore.chips[k].label === shore.category) i = k
              shore.category = shore.chips[(i + 1) % shore.chips.length].label
              e.accepted = true
            }
          }
        }
      }
    }

    // category chips
    Row {
      spacing: 8
      Repeater {
        model: shore.chips
        delegate: Rectangle {
          required property var modelData
          readonly property bool on: shore.category === modelData.label
          width: chipText.implicitWidth + 28
          height: 30
          radius: 15
          color: on ? Theme.accent : chipMouse.containsMouse ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(1, 1, 1, 0.04)
          border.width: on ? 0 : 1
          border.color: Qt.rgba(1, 1, 1, 0.08)
          Behavior on color { ColorAnimation { duration: 140 } }
          Text {
            id: chipText
            anchors.centerIn: parent
            text: modelData.label
            font { family: Theme.font; pixelSize: 12; bold: on }
            color: on ? Theme.bg : Theme.fg
          }
          MouseArea {
            id: chipMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: { shore.category = modelData.label; input.forceActiveFocus() }
          }
        }
      }
    }

    // the grid
    GridView {
      id: grid
      Layout.fillWidth: true
      Layout.fillHeight: true
      clip: true
      cellWidth: 132
      cellHeight: 130
      model: shore.shown
      boundsBehavior: Flickable.StopAtBounds

      delegate: Item {
        id: tile
        required property var modelData
        required property int index
        readonly property bool hot: shore.sel === index
        width: grid.cellWidth
        height: grid.cellHeight

        // rise into place, one after another
        property real appear: 0
        opacity: appear
        transform: Translate { y: (1 - tile.appear) * 26 }
        SequentialAnimation on appear {
          running: true
          PauseAnimation { duration: Math.min(tile.index * 16, 520) }
          NumberAnimation { from: 0; to: 1; duration: 380; easing.type: Easing.OutCubic }
        }

        Rectangle {
          id: plate
          width: 76; height: 76
          radius: 20
          anchors.horizontalCenter: parent.horizontalCenter
          y: hot ? 8 : 12
          Behavior on y { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
          color: hot ? Theme.a(Theme.accent, 0.13) : Qt.rgba(1, 1, 1, 0.045)
          border.width: hot ? 2 : 1
          border.color: hot ? Theme.accent : Qt.rgba(1, 1, 1, 0.07)
          Behavior on color { ColorAnimation { duration: 140 } }
          Image {
            anchors.centerIn: parent
            width: 46; height: 46
            source: Theme.iconFor(modelData)
            sourceSize: Qt.size(92, 92)
            fillMode: Image.PreserveAspectFit
            asynchronous: true
          }
        }
        Text {
          anchors { top: plate.bottom; topMargin: 9; horizontalCenter: parent.horizontalCenter }
          width: grid.cellWidth - 12
          horizontalAlignment: Text.AlignHCenter
          text: modelData.name
          wrapMode: Text.WordWrap
          maximumLineCount: 2
          elide: Text.ElideRight
          font { family: Theme.font; pixelSize: 11 }
          color: hot ? Theme.bright : Theme.fg
        }
        MouseArea {
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onEntered: shore.sel = index
          onClicked: shore.launch(modelData)
        }
      }
    }

    Text {
      visible: shore.shown.length === 0
      Layout.alignment: Qt.AlignHCenter
      text: "Nothing on this stretch of shore."
      font { family: Theme.font; pixelSize: 13 }
      color: Theme.dim
    }
  }

  // hint along the bottom
  Text {
    anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: parent.height * 0.05 }
    opacity: shore.opened ? 0.6 : 0
    text: "type to search  ·  arrows to move  ·  tab for categories  ·  enter to launch  ·  esc to close"
    font { family: Theme.font; pixelSize: 11 }
    color: Theme.dim
  }
}

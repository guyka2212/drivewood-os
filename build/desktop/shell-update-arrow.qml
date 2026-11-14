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


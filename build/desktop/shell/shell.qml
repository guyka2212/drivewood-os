import QtQuick
import Quickshell
import Quickshell.Io

// Drivewood shell: Driftline (bar), Tide (Super menu), Shoreline (apps).
ShellRoot {
  Variants {
    model: Quickshell.screens
    Bar {
      required property var modelData
      screen: modelData
      onMenuRequested: tide.toggle()
      onAppsRequested: shoreline.toggle()
    }
  }

  Tide {
    id: tide
    onAppsRequested: { tide.close(); shoreline.show() }
  }

  Shoreline { id: shoreline }

  IpcHandler {
    target: "drivewood"
    function menu(): void { shoreline.close(); tide.toggle() }
    function apps(): void { tide.close(); shoreline.toggle() }
    function close(): void { tide.close(); shoreline.close() }
    function debug(): string {
      var all = DesktopEntries.applications.values
      var sample = all.length ? (all[0].id + " noDisplay=" + all[0].noDisplay) : "none"
      return "visible=" + Theme.apps().length + " all=" + all.length + " hidden=" + Object.keys(Theme.hidden).length + " first=" + sample
    }
  }
}

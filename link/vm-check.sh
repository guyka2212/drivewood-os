#!/bin/bash
{ pacman -Q python python-gobject gtk4 grim wl-clipboard libnotify openssl base-devel 2>&1
  python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk; print('gtk', Gtk.get_major_version(), Gtk.get_minor_version())" 2>&1
  python3 -c "import cryptography; print('cryptography ok')" 2>&1 | tail -1
  ls -la /dev/uinput 2>&1; ls /var/lib/pacman/sync 2>&1
} | curl -s --data-binary @- http://10.0.2.2:8000/vm-check >/dev/null; echo sent

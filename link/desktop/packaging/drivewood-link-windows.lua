-- DriveWood Link opens as a floating window, never full screen.
o.window({ class = "^org.drivewood.Link$", title = "^DriveWood Link$" }, { float = true, center = true, size = { 540, 600 } })
o.window({ class = "^org.drivewood.Link$", title = "^(Terms of Use|Privacy Policy|Text to .*)$" }, { float = true, center = true, size = { 600, 640 } })
o.window({ class = "^org.drivewood.Link$", title = "^Controlling .*$" }, { float = true, center = true, size = { 1120, 720 } })
o.window({ class = "^org.drivewood.Link$", title = "^DriveWood Link remote control$" }, { float = true, size = { 420, 56 } })

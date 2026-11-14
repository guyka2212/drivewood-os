-- driftwood: tap Super on its own to open the Drivewood menu (replaces Super + Space).
-- A plain release bind: Hyprland cancels it when another key is pressed while
-- Super is held, so Super + key shortcuts keep working without opening the menu.
hl.unbind("SUPER + SPACE")
for _, key in ipairs({ "Super_L", "Super_R" }) do
  o.bind("SUPER + " .. key, "Drivewood menu (tap Super)", "all-settings", { release = true })
end

-- Copilot key: same Drivewood menu, without the old label
hl.unbind("SUPER + SHIFT + code:201")
o.bind("SUPER + SHIFT + code:201", "Drivewood menu", "all-settings")

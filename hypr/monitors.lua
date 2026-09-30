-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
-- List current monitors and supported resolutions with: hyprctl monitors all

local omarchy_gdk_scale = 1
local omarchy_monitor_scale = 1

hl.env("GDK_SCALE", tostring(omarchy_gdk_scale))

-- Render on the NVIDIA dGPU: the HDMI port is wired to it, so this avoids the
-- Intel->NVIDIA frame copies that make Chromium glitch. Only applied once the
-- udev symlinks from /etc/udev/rules.d/61-gpu-names.rules exist.
local nvidia_dgpu = io.open("/dev/dri/nvidia-dgpu")
if nvidia_dgpu then
  nvidia_dgpu:close()
  hl.env("AQ_DRM_DEVICES", "/dev/dri/nvidia-dgpu:/dev/dri/intel-igpu")
end
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = omarchy_monitor_scale })

-- Configure a specific monitor.
-- hl.monitor({ output = "DP-2", mode = "2560x1440@144", position = "0x0", scale = 1 })

-- Portrait/rotated secondary monitor (transform: 1 = 90°, 3 = 270°).
-- hl.monitor({ output = "DP-2", mode = "preferred", position = "auto", scale = 1, transform = 1 })

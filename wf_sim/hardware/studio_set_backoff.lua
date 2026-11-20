--[[
studio_set_backoff.lua: change TX power back-off (E4) without redoing the full setup.
Run only after studio_setup_txbo18.lua finished, and never while a capture is running.
Re-sends Profile (new back-off), both chirps and Frame, with the same values as the setup script.

Use: change BACKOFF below (0, 6, 12, 18), save, then Studio bottom-left Browse -> this file -> Run!.
Check the Output: ProfileConfig line shows the new back-off three times, then "OK" lines.
Worked 2026-11-19 (E4: back-off 0, 6, 12 confirmed in the capture logs).
]]

BACKOFF    = 6     -- dB, all TX. E4: 0, 6, 12, 18
NUM_FRAMES = 20
NUM_LOOPS  = 16
PERIOD_MS  = 100
RX_GAIN    = 30

local ok_all = true
local function step(name, ret)
    if ret == 0 then WriteToLog(name .. ": OK\n", "green"); return true end
    WriteToLog(name .. ": FAILED (" .. tostring(ret) .. ")\n", "red"); ok_all = false; return false
end

local function run()
    WriteToLog("=== studio_set_backoff.lua: back-off " .. BACKOFF .. " dB ===\n", "green")
    -- same profile as studio_setup_txbo18.lua (ramp end 57.1 us, see note there)
    if not step("ProfileConfig (back-off " .. BACKOFF .. ")", ar1.ProfileConfig(0, 77, 429, 7, 57.1,
            BACKOFF, BACKOFF, BACKOFF, 0, 0, 0, 70, 1, 240, 4884, 0, 0, RX_GAIN)) then return end
    if not step("Chirp 0 = TX0 (our TX1)", ar1.ChirpConfig(0, 0, 0, 0, 0, 0, 0, 1, 0, 0)) then return end
    if not step("Chirp 1 = TX2 (our TX3)", ar1.ChirpConfig(1, 1, 0, 0, 0, 0, 0, 0, 0, 1)) then return end
    if not step("FrameConfig (" .. NUM_FRAMES .. " frames)",
            ar1.FrameConfig(0, 1, NUM_FRAMES, NUM_LOOPS, PERIOD_MS, 0, 0, 1)) then return end
end

run()
if ok_all then
    WriteToLog("=== Back-off " .. BACKOFF .. " dB set. Now: new path -> ARM -> Trigger ===\n", "green")
else
    WriteToLog("=== Stopped at the FAILED step above ===\n", "red")
end

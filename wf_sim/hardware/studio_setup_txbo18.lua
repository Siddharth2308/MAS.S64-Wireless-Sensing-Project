--[[
studio_setup_txbo18.lua: one-click mmWave Studio setup for IWR1443BOOST + DCA1000.

Does: reset -> RS232 connect -> BSS/MSS firmware -> SPI connect -> RF power-up ->
static config -> RF init -> data path / LVDS -> profile, both chirps, frame ->
DCA1000 setup. It does NOT capture. After it finishes: DCA1000 ARM, wait 2 s,
Trigger Frame (GUI buttons), as in experiment.md.

Settings = experiment.md / studio_iwr1443_txbo18.xml / iwr1443_txbo18.cfg.
API calls copied from TI's Scripts/DataCaptureDemo_xWR.lua and Automation.lua,
and from the calls Studio logged when the GUI setup worked on 2026-11-19.
First runs 2026-11-19: OK up to ProfileConfig (VCO range); ramp end now 57.1 us.

Before running:
  - Jumpers in dev mode (SOP0 + SOP1 closed, SOP2 open), both boards powered,
    NRST pressed, Studio opened as administrator, No. of Devices Detected = 1.
  - Connection tab: 77 GHz and XWR14xx selected.
Run: bottom-left of Studio, Browse -> this file -> Run!. Watch the Output window.
If the connect step fails: click Set (1) and Connect (2) in the GUI, set
DO_CONNECT = false below, and run again.
]]

------------------------------ settings ----------------------------------------
DO_CONNECT   = true          -- false if RS232 is already connected in the GUI
COM_PORT     = 24            -- XDS110 Application/User UART
BAUD         = 115200        -- what the GUI used successfully

STUDIO       = "C:\\ti\\mmwave_studio_02_01_01_00"
BSS_FW       = STUDIO .. "\\rf_eval_firmware\\radarss\\xwr12xx_xwr14xx_radarss.bin"
MSS_FW       = STUDIO .. "\\rf_eval_firmware\\masterss\\xwr12xx_xwr14xx_masterss.bin"

TX_BACKOFF   = 18            -- dB, all TX (E4 changes this: 0, 6, 12, 18)
RX_GAIN      = 30            -- dB
NUM_FRAMES   = 20            -- per capture (E0/E1: 100, E2: 600, E5: 20)
NUM_LOOPS    = 16
PERIOD_MS    = 100

PC_IP        = "192.168.33.30"
DCA_IP       = "192.168.33.180"
DCA_MAC      = "12:34:56:78:90:12"

------------------------------ helpers -----------------------------------------
local ok_all = true

local function step(name, ret)
    if ret == 0 then
        WriteToLog(name .. ": OK\n", "green")
        return true
    end
    WriteToLog(name .. ": FAILED (" .. tostring(ret) .. ")\n", "red")
    ok_all = false
    return false
end

-- calls that some Studio versions don't return 0 for; log but don't stop
local function try(name, f)
    local good, err = pcall(f)
    if not good then WriteToLog(name .. ": skipped (" .. tostring(err) .. ")\n", "red") end
end

------------------------------ sequence ----------------------------------------
local function run()
    WriteToLog("=== studio_setup_txbo18.lua ===\n", "green")

    -- Connection tab
    if DO_CONNECT then
        try("FullReset", function() ar1.FullReset() end)
        RSTD.Sleep(500)
        if not step("SOPControl(2) dev mode", ar1.SOPControl(2)) then return end
        RSTD.Sleep(500)
        if not step("RS232 Connect COM" .. COM_PORT, ar1.Connect(COM_PORT, BAUD, 1000)) then return end
        RSTD.Sleep(1000)
    end
    try("frequencyBandSelection", function() ar1.frequencyBandSelection("77G") end)
    try("SelectChipVersion", function() ar1.SelectChipVersion("XWR1443") end)

    if not step("BSS firmware", ar1.DownloadBSSFw(BSS_FW)) then return end
    RSTD.Sleep(2000)
    if not step("MSS firmware", ar1.DownloadMSSFw(MSS_FW)) then return end
    RSTD.Sleep(2000)
    if not step("SPI Connect (PowerOn)", ar1.PowerOn(0, 1000, 0, 0)) then return end
    if not step("RF Power-up (RfEnable)", ar1.RfEnable()) then return end

    -- StaticConfig tab: TX0 + TX2 (our TX1, TX3), RX0-3, 16 bit, complex 1x, no IQ swap
    if not step("ChanNAdcConfig", ar1.ChanNAdcConfig(1, 0, 1, 1, 1, 1, 1, 2, 1, 0)) then return end
    if not step("LPModConfig (regular ADC)", ar1.LPModConfig(0, 0)) then return end
    if not step("RfInit", ar1.RfInit()) then return end
    RSTD.Sleep(1000)

    -- DataConfig tab: LVDS, ADC data, 4 lanes
    if not step("DataPathConfig", ar1.DataPathConfig(1, 1, 0)) then return end
    if not step("LvdsClkConfig", ar1.LvdsClkConfig(1, 1)) then return end
    if not step("LVDSLaneConfig (4 lanes)", ar1.LVDSLaneConfig(0, 1, 1, 1, 1, 1, 0, 0)) then return end

    -- SensorConfig tab
    -- ProfileConfig(id, startGHz, idle_us, adcStart_us, rampEnd_us,
    --   tx0/tx1/tx2 backoff dB, tx0/tx1/tx2 phase, slope MHz/us, txStart_us,
    --   samples, ksps, hpf1, hpf2, rxGain dB)
    -- Ramp end 57.1 us, not 57.14: Studio rounds slope 70 to its hardware step
    -- (70.006), and 77 + 70.006*57.14/1000 = 81.0001 GHz is past the 81 GHz VCO
    -- limit -> "RAMP END FREQUENCY IS NOT WITHIN VCO RANGE" (2026-11-19).
    -- 57.1 ends at 80.997 GHz. ADC window is unchanged (7 + 240/4.884 = 56.1 us),
    -- so the sampled band and dca_process are unaffected.
    if not step("ProfileConfig", ar1.ProfileConfig(0, 77, 429, 7, 57.1,
            TX_BACKOFF, TX_BACKOFF, TX_BACKOFF, 0, 0, 0,
            70, 1, 240, 4884, 0, 0, RX_GAIN)) then return end
    -- ChirpConfig(start, end, profile, fVar, slopeVar, idleVar, adcVar, tx0, tx1, tx2)
    if not step("Chirp 0 = TX0 (our TX1)", ar1.ChirpConfig(0, 0, 0, 0, 0, 0, 0, 1, 0, 0)) then return end
    if not step("Chirp 1 = TX2 (our TX3)", ar1.ChirpConfig(1, 1, 0, 0, 0, 0, 0, 0, 0, 1)) then return end
    -- FrameConfig(chirpStart, chirpEnd, frames, loops, period_ms, trigDelay, 0, trigger 1 = SW)
    if not step("FrameConfig", ar1.FrameConfig(0, 1, NUM_FRAMES, NUM_LOOPS, PERIOD_MS, 0, 0, 1)) then return end

    -- DCA1000 (Set Up DCA1000 window)
    if not step("SelectCaptureDevice", ar1.SelectCaptureDevice("DCA1000")) then return end
    if not step("DCA EthInit", ar1.CaptureCardConfig_EthInit(PC_IP, DCA_IP, DCA_MAC, 4096, 4098)) then return end
    -- Mode(eth stream, xWR12xx/14xx = 1, raw/LVDS = 1, 2, 3, 30): TI's values for this chip
    if not step("DCA Mode", ar1.CaptureCardConfig_Mode(1, 1, 1, 2, 3, 30)) then return end
    if not step("DCA PacketDelay 25 us", ar1.CaptureCardConfig_PacketDelay(25)) then return end
end

run()
if ok_all then
    WriteToLog("=== Setup done. Now: DCA1000 ARM -> wait 2 s -> Trigger Frame ===\n", "green")
else
    WriteToLog("=== Setup stopped at the first FAILED step above ===\n", "red")
end

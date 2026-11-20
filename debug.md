# Windows debug: DCA1000 + IWR1443BOOST

Values marked (verify) are from memory or one forum log; check them against TI's DCA1000 Quick Start Guide.

## Check first
- Both boards powered (5 V, 2.5 A each); board LEDs on.
- Ethernet cable connected directly to the PC.
- Close the TI Visualizer, serial terminals and anything else using the COM ports.
- After any failure: press NRST, power-cycle both boards, reopen Studio.

## Device Manager
- **Expected, IWR:** XDS110 Class Application/User UART and XDS110 Class Auxiliary Data Port.
- **Expected, DCA1000:** four FTDI "AR-DevPack-EVM-012" ports (COM27-30 on this PC), from the RADAR_FTDI USB.
- **Unknown device or yellow warning:**
  - Replug USB, try another port and cable.
  - XDS110: install UniFlash or TI's emupack drivers.
  - FTDI: install the drivers from the mmWave Studio folder.
  - Then replug.
- **COM port "access denied":** another program has it. Close it or reboot.
- **Port numbers changed:** normal after changing USB ports. Reselect them in Studio. For the logger, pass `--cli COMx --data COMy`.

## Network
- **PC Ethernet adapter:** static IP `192.168.33.30`, mask `255.255.255.0`, no gateway.
- **DCA1000 IP:** `192.168.33.180`, MAC `12:34:56:78:90:12` (confirmed Nov 19).
- **Ping fails: normal.** The DCA only speaks UDP. Check instead: Studio's Setup DCA1000 shows "FPGA Version : 2.9 [Record]", or `arp -a` lists 192.168.33.180.
- **Firewall (our Nov 19 cause of "0 packets"):** Windows sets the DCA link to **Public**, which drops the DCA's data stream. Setup commands still work, because Windows lets replies in. Fix, in admin PowerShell:
  ```powershell
  New-NetFirewallRule -DisplayName "DCA1000 UDP in" -Direction Inbound -Protocol UDP -LocalPort 4096,4098 -RemoteAddress 192.168.33.180 -Action Allow -Profile Any
  ```
  Undo: `Remove-NetFirewallRule -DisplayName "DCA1000 UDP in"`.
- Turn off VPN and any other adapter on `192.168.33.x`.
- **Permissions:** network and firewall changes need admin. Run Studio as administrator if it can't connect.

## mmWave Studio
- **Won't open or crashes:** install MATLAB Runtime **8.5.1** (32-bit) and use the 1st-generation Studio installer.
- **RS232 connect fails:**
  - Jumpers wrong (our Nov 12 cause). Dev mode is **SOP0 and SOP1 closed, SOP2 open**. Power-cycle, then press NRST.
  - Wrong COM port. Use the XDS110 Application/User UART (COM24 on this PC).
- **SPI connect or firmware load fails:**
  - Check jumpers are in Development mode (SOP0 + SOP1 closed, SOP2 open), then power-cycle.
  - Check FTDI drivers (the DCA's RADAR_FTDI USB must be plugged in; FPGA_JTAG USB not needed).
  - Check the firmware matches the board (`xwr12xx_xwr14xx`).
- **"Power on one Device at a time!" on SPI Connect:** No. of Devices Detected = 0. Click refresh until it shows 1.
- **SPI Connect: MSS version 0.0.0.0, PowerOn RESP TIMEOUT, "MSS Power Up async event was not received" (our Nov 19 cause):** erase the board's serial flash.
  1. Jumpers to flash mode: **SOP0 + SOP2 closed**, SOP1 open. Power-cycle.
  2. UniFlash → IWR1443 → COM24 → Settings & Utilities → **Format SFLASH**.
  3. Jumpers back to dev mode, power-cycle, NRST, redo Studio setup.
  - This erases the out-of-box demo. To restore it: flash mode, UniFlash, Meta Image 1 = `C:\ti\mmwave_sdk_02_01_00_04\packages\ti\demo\xwr14xx\mmw\xwr14xx_mmw_demo.bin`, Load Image, then jumpers to SOP0 only.
- **RF Power-up: "RadarAPI read register failed -2":** SPI isn't connected. Fix SPI first.
- **Studio's firmware is in RAM:** after every power-cycle, redo the whole setup. Use `wf_sim\hardware\studio_setup_txbo18.lua` (Browse → Run!). If a step prints red FAILED, fix that step and rerun after a power-cycle + NRST.
- **ProfileConfig "RAMP END FREQUENCY IS NOT WITHIN VCO RANGE" (error 46):** start + slope × ramp end is above 81 GHz. Studio rounds slope 70 to 70.006, so ramp end 57.14 µs gives 81.0001 GHz. Use **57.1 µs**.
- **Setup DCA1000 fails:** check IP, firewall, and that the FTDI ports show in Device Manager.
- **Capture: 0 packets** (`adc_data_Raw_LogFile.csv` says "Number of received packets - 0"): firewall (see Network). If the rule is there, check the DCA switches and the ribbon cable.
- **File picker won't accept a new path:** create an empty file first: `New-Item C:\dca\<label>\adc_data.bin -ItemType File` (make the folder first).
- **PostProc error `calc_rel_offset_and_file_name ... not assigned`:** no data was captured (0 packets). Fix the capture first.
- **PostProc empty or fails:**
  - Press ARM before Trigger each time.
  - Use a short save path with no spaces: `C:\dca\...`.
  - Check MATLAB Runtime and free disk space.
  - Check LVDS is 4 lanes and matches the sample settings.
  - **Our scripts don't need PostProc.** During a capture the DCA writes `adc_data_Raw_0.bin`; a few seconds after "Record is completed" it becomes `adc_data.bin` (seen Nov 19 even when PostProc failed). If `adc_data.bin` is still 0 bytes, wait a few seconds.
  - PostProc's `calc_rel_offset_and_file_name` error also appears when the capture is fine (E3, Nov 19). Check `adc_data.bin` size and `adc_data_Raw_LogFile.csv` instead.

## `dca_process` warnings
- **`complete` = False:** Studio samples/chirps don't match `iwr1443_txbo18.cfg`, or packets were lost. Check settings, then shorten the capture. Use a direct cable and close heavy apps.
- **`rx_peak_bins` differ by one bin** (e.g. `11 12 12 11`) with similar levels: the target sits between two bins. Fine.
- **`rx_peak_bins` disagree by more, or no clear peak:** wrong lanes, sample count or ADC format. Expected: 4 lanes, complex 1x, 16 bit, 240 samples.
- **`clip_pct` > 0:** signal too strong. Lower RX gain or raise TX back-off.
- **Peak in the wrong place:** slope or sample rate differs from the cfg. Compare with Studio's PostProc.
- **Phase jumps:** table vibration, or someone moving in front of the radar.
- **`materials`: "no E5_r_* or E5_t_* captures":** folders must be `E5_r_<sample>_<n>\adc_data.bin`, with no extra underscores in `<sample>`.
- **`materials`: KeyError `alu` or `none`:** each part needs its reference captures (`alu` for reflection, `none` for transmission).

## Python and files
- **`activate` blocked:** run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **`ModuleNotFoundError: hardware` or `sim`:** run from `Project\wf_sim`.
- **Paths with spaces:** wrap them in double quotes.
- **`python` opens the Microsoft Store:** use `py`, or turn off the app execution alias.
- **Repo shows every file as changed:** run `git config core.autocrlf false` and `git config core.filemode false`.
- **Drive won't open on Linux afterwards:** turn off Windows Fast Startup, and shut down Windows fully.

## Still stuck
Send Claude the exact error, Studio's Output window text, and a Device Manager screenshot.

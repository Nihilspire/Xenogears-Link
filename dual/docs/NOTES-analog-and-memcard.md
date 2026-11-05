# Investigation notes (Oct 22-23 2026)

## Analog controls "froze on load" (0.3/0.4) and STOOD DOWN (0.14)
- Not reproducible in emulation: x86 interpreter, ARM ari64 under qemu, HLE and OpenBIOS, boot -> title ->
  New Game -> Fei's room, Continue screen; all fine with the cheat engine and with the frontend installer.
- The block 0x80017400-0x80017C84 is zero in SLUS_006.64 and SLUS_006.69 on disc (it sits after the disc
  file table at 0x80010000-0x80017188), no game code references it, and it stayed zero in RAM across 10
  ePSXe cutscene states spanning Disc 1.
- On Jack's device 0.14 reported STOOD DOWN (block not empty, not our program); 0.15 added replace-if-same-
  program and skipping user mods that write there, after which analog movement + tilt-to-run worked.
  The exact source of the foreign bytes was never captured.

## Right stick / smooth L1-R1 never worked
- Payload guard `free_cam` requires CAMERA_MODE == 0, declared `uint32_t` at 0x800AF934. The field code
  only accesses 0x800AF934 with `sh` and 0x800AF936 separately (`sh`/`lh`), so it's a halfword; in Fei's
  room 0x800AF936 = 0x0019, so the 32-bit read was never 0.
- Fix: `lw $t5,-0x6cc($t2)` at 0x8001785C -> `lhu` (word 8D4DF934 -> 954DF934). After it, right stick orbits
  (yaw 40, 88, 184, ...), tilt goes 25° -> 55°, L1 turns in 40-unit steps instead of the stock 45° jump.

## "Memory card is not formatted" (built-in BIOS)
- Repro: load `lh_loaded.state` (a real save loaded at a save point), File > Save > a free block ->
  "The Memory Card in Slot 1 is not formatted." Loading and deleting from the title screen worked.
- Cause (HLE BIOS call log): `_card_info` delivers EvSpNEW (0x2000) whenever `McdFlag[port] & 8`. The core
  sets that bit in LoadMcd, sioReset and on every state load (sioFreeze), and the HLE BIOS only clears it on a
  write; Xenogears' save path treats "new card" as unformatted and never writes.
- Fix: export `McdFlag` from the core and clear bit 8 of both slots before each `retro_run`. Saving then works
  ("This block is free. Save?" -> new BASLUS-006641 entry), on x86 and ARM.

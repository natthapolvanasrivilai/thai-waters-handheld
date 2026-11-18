# Thai Waters · Firmware 0.3

For Waveshare ESP32-S3-Touch-LCD-3.5B (31137), QMI8658, ES8311 and a right-side AS5600 reel at 0x36. The optional DRV2605L at 0x5A adds haptics. The game runs without the haptic module. The bench guide in this folder includes wiring, optional BOM and candidate placement.

## Flash and play

Extract the ZIP. With the board connected by a USB data cable and the serial monitor closed, substitute the actual port for COM7. Flashing replaces the active game. These four writes leave the existing NVS partition in place with the project’s v0.1 partition layout.

~~~powershell
python -m pip install esptool==5.3.0
.\Flash-Thai-Waters.ps1 -Port COM7
~~~

On other operating systems use the corresponding serial port in the command below.

~~~sh
python -m esptool --chip esp32s3 --port COM7 write-flash --flash-mode dio --flash-freq 80m --flash-size 16MB 0x0 flash/bootloader.bin 0x8000 flash/partitions.bin 0xe000 flash/boot_app0.bin 0x10000 flash/ThaiWaters.bin
~~~

Hold BOOT, tap RESET, then release BOOT if the board needs download mode. Boot diagnostics are available at 115200 baud. On first boot with a new board, follow the two-pose calibration. A v0.1 installation with saved poses and sound preferences reuses them. Gameplay catches in v0.1 were session-only. A fresh installation starts a persistent field book.

Open Menu from the game. Select Fishing spots and use the arrows to browse 117 destinations. Select a spot and time, then Fish here. Live follows the Bangkok clock. The rod follows calibrated tilt continuously. Raise and sweep to cast, lift on the bite and ease off during runs. The gripped right-side AS5600 drives the reel. The catch screen shows a white-edged sprite, rarity, length, game-derived weight and fictional origin. The Fish collection records 52 species. Visit the Rod workshop to fit upgrades, refund points or choose a finish. The 0.2 journal and ranks migrate on first successful save. Existing 0.1 poses and sound settings can be reused.

Menu → Wi-Fi + clock provides phone provisioning, live time, an owner-configured signed release feed, and LAN shared events. See Interfaces.md and Bench-guide.md. The desktop/mobile practice game and local event host are in the private project repository. The user-facing simulator uses the actual Rev E external CAD, a live LCD and a folding, mouse-driven right-side crank.

## Build and verification

Extract the libraries directory from ../releases/prototypes/Thai-Waters-firmware-0.3.zip alongside the sketch to use the build command below. The source sketch directory retains its v0.1 name for existing build workflows. Use Arduino CLI 1.3.1 and Arduino-ESP32 3.3.10. Waveshare's library revision is c7dd63c70258da7e3b6dae0c621f30ca62b1e1c9.

~~~sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.10 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli compile --fqbn "esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,FlashMode=qio,PartitionScheme=app3M_fat9M_16MB,USBMode=hwcdc,CDCOnBoot=cdc" --libraries libraries WillowCreek
~~~

The archive contains the target image, hash manifest, partition segments, source, vendor libraries and verification records. The target build and host simulations passed. Physical RF, charging, on-device updates, clock holdover, audio, rumble, sensor alignment, simultaneous handheld play and production approval remain open.


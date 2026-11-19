# Phone play and shared fishing events

Use Node 20+ on a computer on the same Wi-Fi as the phones and Rev E units. The computer hosts the game and the three-minute cooperative events. It serves the game to invited browsers and keeps event scores in memory. Closing the host ends the event.

~~~powershell
npm ci
$env:TW_HOST = 'your-computer-name-on-the-LAN'
$env:TW_CERT = 'C:\path\to\trusted-server-chain.pem'
$env:TW_KEY = 'C:\path\to\server-private-key.pem'
npm start
~~~

The server certificate must match TW_HOST and be trusted by the testing phone. Open the pairing page on the host computer at **https://localhost:8443/pair** and scan its QR code. If the certificate does not cover localhost, use a trusted certificate with both the LAN name and localhost for this setup. The invite rotates whenever the host restarts. Set TW_QR to a local PNG filename before starting to export it. Keep that PNG and TLS keys outside Git.

**Phone motion** — Open **Menu → Motion bench → Enable phone motion**. Allow sensor access when the browser prompts. Capture rest, raise the far edge 30–50°, hold still, and capture lift. Resume and lower the phone to establish the low pose. Raise and sweep down to cast. On a bite, lift to hook. Move through small angles to verify that the tip follows continuously. Drag the dial in circles to wind, and ease off during a run. The displayed gravity is in g and rotation is in degrees/s. Missing or denied sensors leave the touch controls available.

**Shared event** — Select the same named spot, then **Menu → Shared event → Join event**. Connect each handheld to the same Wi-Fi and select **Menu → Wi-Fi + clock → Shared event**. The first participant starts a three-minute round. The goal is eight combined landings. The host reports active participants, remaining time and cumulative catches. Duplicate packets do not add points. Each device keeps its own journal and tackle progression. The host uses TCP 8443 for browser play and UDP 42438 on the LAN for handheld discovery and score updates. A guest network with client isolation can prevent devices from joining.

**Sensor correspondence** — The browser runs the handheld's two-pose projection, 70% lift threshold, 27% return threshold and 900 ms cast interval through WebAssembly. It divides accelerationIncludingGravity by 9.80665 to convert m/s² to g. The browser's rotationRate is diagnostic. Its axes and cadence depend on the handset. The touch wheel quantizes one revolution to 4096 positions and passes deltas through the same unwrap logic. Only the real AS5600 can validate magnet strength, alignment and the manufactured handle. Use the real board bench to verify these and compare QMI8658 readings through USB.

**Verify** — npm test starts an isolated loopback host, joins two HTTP sessions and one simulated handheld UDP client, then checks a shared goal and room isolation. A trusted HTTPS LAN session, two physical phones, and two finished handhelds are separate acceptance tests. On a developer computer without a certificate, launching with TW_CERT and TW_KEY unset provides an HTTP desktop test mode.

[Device motion permission and secure contexts](https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent/requestPermission_static)


The daily specimen cup needs Node 22.13+ with SQLite. Set TW_CUP_DB to choose its database path. The host shares one daily board across paired browsers and TWCR-capable handhelds.

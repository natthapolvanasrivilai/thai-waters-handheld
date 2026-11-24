POCKET REEL SOLO FOR WINDOWS
Offline launcher. Not an installer.

Extract the whole ZIP into a folder. Verify the ZIP SHA-256 against
the matching release record, not just the manifest inside the ZIP.
From that folder, in PowerShell with Node.js 22 or later, run:
  node .\Start-Pocket-Reel-Solo.mjs

Only after the launcher reports that it is listening, open:
  http://127.0.0.1:17841/
If the port is occupied, stop. Do not visit that address until this
launcher starts successfully, and do not substitute another port.
Keep the launcher running while playing. Ctrl+C stops it.

Use the same normal browser profile and exact address every time.
Do not use an incognito window, localhost, another port, or the HTML
file directly if you want to reopen the same Solo save. An older
direct-file save is separate; it is never imported automatically.
To move it, export from Career in the old game, keep that backup,
then explicitly import the backup in Solo. Verify your journal before
discarding anything. If the source reports Recovery, do not overwrite
it with a fresh game. Keep the original file and backups.

Before replacing the launcher, export and keep a backup via Career.
Keep the old verified ZIP. Unpack the new ZIP into a separate folder,
close the old launcher, and start the new one before opening that
same address in the same profile. Check the journal. If it does not
look right, stop before playing or writing a new save. Reopen the old
verified package on the same origin; use explicit restore only after
checking that your backup is readable and correct. A newer save may
not be compatible with an older game; keep the pre-update backup.

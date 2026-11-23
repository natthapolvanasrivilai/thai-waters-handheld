#!/usr/bin/env bash
set -euo pipefail
umask 077
repo="$(cd "${1:?Pass the exact scratch checkout}" && pwd -P)"
html="$(realpath "${2:?Pass the verified main packed HTML}")"
out="$(realpath "${3:?Pass an existing private empty output directory}")"
here="$(cd "$(dirname "$0")" && pwd -P)"
source=f08e82693c259f505d848f91298bd60ae239d662
html_sha=0f87d0c63afd86d97602b401967a8c13d75aabfda9a674e6d16a17efc3457f2e
[[ "$(git -C "$repo" rev-parse HEAD)" = "$source" ]]
[[ -d "$out" && -z "$(find "$out" -mindepth 1 -maxdepth 1 -print -quit)" ]]
printf '%s  %s\n' "$html_sha" "$html" | sha256sum -c --status -
node_path="$repo/verification/browser-tests/node_modules"
export NODE_PATH="$node_path"
node -e 'let a=require.resolve("playwright-core"); if(!a.startsWith(process.env.NODE_PATH+"/"))throw Error("exact repo npm ci required");'
[[ "$(node -p 'require("playwright-core/package.json").version')" = 1.62.1 ]]
[[ "$(node --version)" = v22.16.0 ]]
BROWSER_PATH="$(node -p 'require("playwright-core").chromium.executablePath()')"
export BROWSER_PATH
[[ -x "$BROWSER_PATH" ]]
printf 'SOURCE_COMMIT=%s\nHTML_SHA256=%s\n' "$source" "$html_sha" > "$out/inputs.txt"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/verification/browser-tests" "$tmp/game"
for p in verification/browser-tests/location-map.cjs verification/browser-tests/boot-home-check.cjs game/locations.json; do
  git -C "$repo" show "$source:$p" > "$tmp/$p"
done
(cd "$tmp" && patch --dry-run --silent --forward -p1 < "$here/diagnostic.patch" && patch --silent --forward -p1 < "$here/diagnostic.patch")
cp "$html" "$tmp/game/Thai-Waters-play.html"
node --check "$tmp/verification/browser-tests/location-map.cjs"
node --check "$here/file-storage-fixture.cjs"
fixture=0
app=0
FIXTURE_CYCLES=2 FIXTURE_LANES=mobile,desktop,touch-only,mobile-only timeout 180 node "$here/file-storage-fixture.cjs" > "$out/fixture.log" 2>&1 || fixture=$?
timeout 360 node "$tmp/verification/browser-tests/location-map.cjs" "$tmp/game/Thai-Waters-play.html" > "$out/app.log" 2>&1 || app=$?
printf 'fixture=%d\napp=%d\n' "$fixture" "$app" | tee "$out/exit-status.txt"
if [[ "$app" = 0 ]]; then
  grep -Fxq "TW_LANE file $html_sha" "$out/app.log" || exit 2
fi
((fixture == 0 && app == 0))

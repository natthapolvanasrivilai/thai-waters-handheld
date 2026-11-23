# Ping River scenery: destination 52

The original layered scene represents an upstream view on the Ping River near Nawarat Bridge, Chiang Mai. It is stylized, not live imagery, a surveyed skyline, an access point, or a statement that fishing is permitted. The bank, vegetation, and distant building silhouettes are original generic details, not individually identified landmarks. The bridge itself is the reference vantage, not a landmark asserted visible in the scene.

- Royal Irrigation Department [station register](https://water.rid.go.th/hyd/download/List_Station.pdf): P.1, Ping River, Nawarat Bridge, Chiang Mai, 18.786925° N, 99.004725° E. The [station record](https://water.rid.go.th/hyd/download/book2012/assets/basic-html/page218.html) describes the gauge on the left bank roughly 100 m downstream of the bridge. The gauge coordinate is not the viewpoint or a playable access point.
- MikSed's [documented bridge viewpoint](https://commons.wikimedia.org/wiki/File:%D0%A0%D0%B5%D0%BA%D0%B0_%D0%9F%D0%B8%D0%BD%D0%B3_(20260423110434).jpg), 23 April 2026, heading 315°, CC BY-SA 4.0, identifies the upstream view. Metadata supports orientation only. The photo, its pixels, and any traced or adapted geometry are not included.

The scene keeps the existing day, weather, and reduced-motion options. Reduced motion freezes only the extra Ping current accents. The location ID, labels, casting zones, playable inputs, and saves retain their existing definitions. Any navigation or place access should be verified separately outside the game.

## Build verification

The release workflow rebuilds both modules with its pinned Zig and checks their exact bytes inside the packed HTML. The new scene ABI requires the two world tests' independently read landscape hashes. A pre-change source is supported only if it is an ancestor of the last reviewed historical commit, uses the old two-argument scene ABI, and matches the workflow's existing canonical test partition. Its report explicitly uses `historical-artifact-only` rather than claiming direct test receipts. Only the source checkouts of the browser test and aggregate jobs need full commit ancestry; blob filtering avoids pulling historical asset blobs. Older, incompatible test suites need a matching historical workflow and harness.

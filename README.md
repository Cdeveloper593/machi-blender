# MACHI まち — a scroll-world demo (Blender edition)

One small clay-diorama Japanese town, one whole day. Scroll, and the camera
flies through Machi in a single continuous take — morning arrival over the
town island, the shotengai shopping street, the canal at golden hour, shrine
steps at dusk, the night market, and a finale inside the glow of a giant
paper lantern.

## How it works

- Rendered in Blender 5.2 (Eevee via software GL) — no AI video, zero AI
  credits used.
- One continuous camera flight split into 11 segments (6 scene dives + 5
  aerial connectors) with shared boundary frames: every segment ends on the
  exact frame the next one starts from, so the seams are pixel-identical
  (verified by PSNR: all 10 boundaries measure infinite dB, MSE 0).
- The town is a procedural clay diorama built by `build_town.py`
  (`machi.blend`): island, streets, canal, shrine, market stalls, lanterns
  and the giant paper lantern, all modelled and lit in Blender.
- A scroll-scrub engine (`scrub-engine.js`) maps scroll position to video
  time across the whole chain — no cuts, no autoplay.
- Clips are encoded for scrubbing at 720p, crf 20, GOP 8, faststart, with a
  light unsharp pass.
- Static site, no build step: open `index.html` or serve the folder.

## Build

- `build_town.py` — builds the procedural town into `machi.blend`.
- `render_chunks.sh A|B` — renders the 11 segments in resumable 48-frame
  chunks (worker A: dives, worker B: connectors) into `renders/`.
- `encode_all.sh` — encodes the rendered frames into `site/assets/vid/`.

## Credits

Total generation cost: 0 credits — rendered locally in Blender (plus a
Google Colab T4 worker on the final segments), no AI video generation.

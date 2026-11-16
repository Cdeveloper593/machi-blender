#!/bin/bash
# Chunked, resumable segment renderer. Usage: render_chunks.sh A|B
# Worker A renders the dives, worker B the connectors.
# NOTE 2026-11-15: Blender must run under xvfb-run (GLX path). Headless EGL is
# broken on this VM (libEGL.so.1 missing; extracted Mesa EGL crashes in
# eglGetPlatformDisplay), so plain background Blender aborts every chunk. Chunks of 48 frames;
# a chunk is skipped when all its PNGs already exist.
set -u
cd "$(dirname "$0")"
export LIBGL_ALWAYS_SOFTWARE=1
BLENDER=~/workspace/tools/blender-current/blender
WORKER="${1:?usage: render_chunks.sh A|B}"
if [ "$WORKER" = "A" ]; then
  SEGMENTS="dive1:0:192 dive2:384:576 dive3:768:960 dive4:1152:1344 dive5:1536:1728 dive6:1920:2112"
else
  SEGMENTS="conn1:192:384 conn2:576:768 conn3:960:1152 conn4:1344:1536 conn5:1728:1920"
fi
CHUNK=48
for seg in $SEGMENTS; do
  IFS=: read -r name start end <<< "$seg"
  mkdir -p "renders/$name"
  f=$start
  while [ "$f" -le "$end" ]; do
    ce=$((f + CHUNK - 1)); [ "$ce" -gt "$end" ] && ce=$end
    missing=0
    for ((i = f; i <= ce; i++)); do
      printf -v fn "renders/%s/f_%04d.png" "$name" "$i"
      [ -f "$fn" ] || { missing=1; break; }
    done
    if [ "$missing" -eq 0 ]; then
      echo "[$WORKER] SKIP $name $f-$ce"
    else
      echo "[$WORKER] RENDER $name $f-$ce $(date +%H:%M:%S)"
      /usr/bin/xvfb-run -a "$BLENDER" -b machi.blend -o "renders/$name/f_" -s "$f" -e "$ce" -a > /dev/null 2>&1
      echo "[$WORKER] DONE $name $f-$ce ($(ls renders/$name/*.png | wc -l) total) $(date +%H:%M:%S)"
    fi
    f=$((ce + 1))
  done
done
echo "[$WORKER] ALL DONE"

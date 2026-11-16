#!/bin/bash
# Render all 11 segments of the MACHI Blender flight as PNG sequences.
# Segments share boundary frames, so seams are exact by construction.
set -u
cd "$(dirname "$0")"
BLENDER=~/workspace/tools/blender-current/blender
mkdir -p renders
SEGMENTS="dive1:0:192 conn1:192:384 dive2:384:576 conn2:576:768 dive3:768:960 conn3:960:1152 dive4:1152:1344 conn4:1344:1536 dive5:1536:1728 conn5:1728:1920 dive6:1920:2112"
for seg in $SEGMENTS; do
  IFS=: read -r name start end <<< "$seg"
  mkdir -p "renders/$name"
  have=$(ls "renders/$name"/*.png 2>/dev/null | wc -l)
  if [ "$have" -ge 193 ]; then echo "SKIP $name (already $have frames)"; continue; fi
  echo "=== RENDER $name frames $start-$end ==="
  "$BLENDER" -b machi.blend -o "renders/$name/f_" -s "$start" -e "$end" -a 2>&1 | grep -E "Saved|Error|error" | tail -2
  echo "=== $name done: $(ls renders/$name/*.png | wc -l) frames ==="
done
echo "ALL SEGMENTS RENDERED"

#!/usr/bin/env bash
# Rough storyboard cut for Pulse-0G.
#
# Purpose: show the narrative order the delivered video is missing. It is not a
# final motion piece — it is real product screens with slow push-ins plus the one
# segment of the delivered video that already works (the claim verifier).
#
#   ./tools/make_v2_cut.sh [delivered_video]
set -euo pipefail
cd "$(dirname "$0")/.."

DELIVERED="${1:-docs/deliverables/pulse_0g_1080p.mp4}"
OUT="docs/deliverables/pulse_0g_v2_storyboard.mp4"
TMP="docs/video/v2"
SANS=/usr/share/fonts/TTF/DejaVuSans-Bold.ttf
MONO=/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf
S=docs/screens
BG=0x0A0E13
# Frame layout: the screen occupies the top 940 px, a caption band the rest.
PH=940
CAPTION_Y=985

# enc <output> <inputs and filters...>
enc() {
  local out="$1"; shift
  ffmpeg -v error -y "$@" -r 30 -c:v libx264 -crf 18 -pix_fmt yuv420p -an "$out"
}

plate() {  # plate <image> <crop> <seconds> <caption>
  local img="$1" crop="$2" dur="$3" cap="$4"
  local frames=$(python3 -c "print(int($dur*30))")
  enc "$TMP/tmp.mp4" -i "$img" -vf "crop=$crop,scale=1920:$PH,\
zoompan=z='min(zoom+0.0009,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$frames:s=1920x${PH}:fps=30,\
pad=1920:1080:0:0:color=$BG,\
drawtext=fontfile=$SANS:text='$cap':fontsize=44:fontcolor=0xE5E7EB:x=90:y=$CAPTION_Y" -t "$dur"
}

# 1 · the problem, on black
enc "$TMP/01.mp4" -f lavfi -i "color=c=$BG:s=1920x1080:r=30:d=3.2" \
  -vf "drawtext=fontfile=$SANS:text='250 million miles.':fontsize=64:fontcolor=0xE5E7EB:x=(w-tw)/2:y=(h-th)/2-40,\
drawtext=fontfile=$SANS:text='No doctor.':fontsize=64:fontcolor=0xF87171:x=(w-tw)/2:y=(h-th)/2+40"

# 2 · the product: body map at FD180, one region in action
plate "$S/02-zona-en-rojo.png" "1240:698:40:60" 5 "Tap a body region." ; mv "$TMP/tmp.mp4" "$TMP/02.mp4"

# 3 · the number means something: sleep and the deviation from the crew's own baseline
plate "$S/02-zona-en-rojo.png" "1000:562:370:186" 5.5 "Your number. Your own baseline." ; mv "$TMP/tmp.mp4" "$TMP/03.mp4"

# 4 · the segment of the delivered video that already works
enc "$TMP/04.mp4" -ss 12.4 -to 18.6 -i "$DELIVERED" -vf "scale=1920:1080"

# 5 · escalation: the case package
plate "$S/06-paquete-completo.png" "1010:568:350:686" 5 "Out of range? Export a case file." ; mv "$TMP/tmp.mp4" "$TMP/05.mp4"

# 6 · name
enc "$TMP/06.mp4" -f lavfi -i "color=c=$BG:s=1920x1080:r=30:d=3" \
  -vf "drawtext=fontfile=$MONO:text='PULSE-0G':fontsize=110:fontcolor=0x2DD4BF:x=(w-tw)/2:y=(h-th)/2-30,\
drawtext=fontfile=$SANS:text='No diagnosis. Every claim traced.':fontsize=34:fontcolor=0x94A3B8:x=(w-tw)/2:y=(h-th)/2+70"

: > "$TMP/list.txt"
for n in 01 02 03 04 05 06; do echo "file '$(pwd)/$TMP/$n.mp4'" >> "$TMP/list.txt"; done
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -an -r 30 -movflags +faststart "$OUT"
echo "duration: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
echo "-> $OUT"

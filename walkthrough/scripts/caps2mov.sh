#!/bin/zsh
# usage: caps2mov.sh <caps_dir> <out.mov>
ffmpeg -loglevel error -y -f concat -safe 0 -i "$1/list.txt" -vf "fps=30,format=yuva444p10le" -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le "$2" && echo "wrote $2"

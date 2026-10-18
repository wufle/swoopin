#!/bin/sh
# Build the browser version: ./web/build.sh  ->  build/web/ (index.html + swoopin.apk)
# Test locally with: python -m http.server -d build/web 8080, then open
# http://127.0.0.1:8080 (not "localhost": pygbag then looks for its own dev server)
set -e
cd "$(dirname "$0")/.."
rm -rf build/stage/swoopin
mkdir -p build/stage/swoopin
cp web/main.py build/stage/swoopin/
cp -r swoopin build/stage/swoopin/
rm -rf build/stage/swoopin/swoopin/record.py build/stage/swoopin/swoopin/__pycache__
python web/render_blips.py build/stage/swoopin/swoopin/sounds
cp web/favicon.png build/stage/swoopin/favicon.png
python -m pygbag --build --app_name swoopin --title Swoopin --width 960 --height 540 --icon web/favicon.png build/stage/swoopin
rm -rf build/web && mv build/stage/swoopin/build/web build/web
echo "Built build/web/"

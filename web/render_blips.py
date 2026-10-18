"""Render audio.py's synthesised blips to .ogg files, so the browser build
doesn't have to download numpy. Usage: python web/render_blips.py OUT_DIR"""
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from swoopin.audio import RATE, synth  # noqa: E402

out = Path(sys.argv[1])
for name, x in synth().items():
    data = (np.clip(x * 0.45, -1, 1)).astype(np.float32).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", "-",
                    "-c:a", "libvorbis", "-q:a", "5", str(out / f"{name}.ogg")], input=data, check=True)
    print("rendered", name)

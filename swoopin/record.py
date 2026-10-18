"""Record your own sound straight into the game.

    python -m swoopin.record threat          # dad's line while he takes aim
    python -m swoopin.record shoo            # mum shooing the magpie
    python -m swoopin.record threat --seconds 4
    python -m swoopin.record threat --replace   # throw away earlier takes first
    python -m swoopin.record --list          # what each sound name is used for

Each take is saved as swoopin/sounds/<name><n>.ogg. Several takes of the
same name become variants the game picks between at random. The recording
is trimmed to where you start talking, levelled, faded and played back.
Uses ffmpeg and your default microphone (PulseAudio/PipeWire).
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

SOUND_DIR = Path(__file__).parent / "sounds"
CREDITS = SOUND_DIR / "CREDITS.md"
RATE = 44100

USES = {
    "threat": "the angry dad as he takes aim",
    "eew": "a kid who has just been pooped on",
    "shoo": "a mum shooing the magpie away from her kids",
    "oi": "the angry dad arriving",
    "yell": "the dad when you hit him",
    "grumble": "the dad storming off",
    "mum": "a kid yelling for mum when swooped",
    "scream": "kids screaming / crying",
    "carol": "magpie carol (start of game, wave cleared)",
    "caw": "crow hit", "caaaw": "crows arriving",
    "meow": "cat hit", "hiss": "cat running off",
    "shotgun": "dad's shot", "bang": "swoop hit",
}


def record(seconds, device):
    tmp = Path(tempfile.mkstemp(suffix=".wav")[1])
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "pulse", "-i", device, "-t", str(seconds),
           "-ac", "1", "-ar", str(RATE), str(tmp)]
    proc = subprocess.Popen(cmd)
    t0 = time.time()
    while proc.poll() is None:
        left = seconds - (time.time() - t0)
        bar = "#" * int((seconds - max(0, left)) / seconds * 30)
        print(f"\r  RECORDING  [{bar:<30}] {max(0, left):4.1f}s ", end="", flush=True)
        time.sleep(0.05)
    print()
    if proc.returncode != 0:
        sys.exit("Recording failed: check your microphone (pactl list short sources).")
    return tmp


def load(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def clean(x):
    """Trim to the onset and the end of the voice, level, and fade."""
    x = x - np.mean(x)
    env = np.convolve(np.abs(x), np.ones(512) / 512, mode="same")
    top = np.max(env)
    if top < 1e-3:
        sys.exit("That was silent. Is the right microphone selected and unmuted?")
    on = np.where(env > top * 10 ** (-24 / 20))[0]
    a = max(0, on[0] - int(0.02 * RATE))
    b = min(len(x), on[-1] + int(0.08 * RATE))
    x = x[a:b]
    x *= 10 ** (-1.5 / 20) / (np.max(np.abs(x)) or 1)
    n = len(x)
    fi, fo = min(n, int(0.005 * RATE)), min(n, int(0.06 * RATE))
    x[:fi] *= np.linspace(0, 1, fi)
    x[n - fo:] *= np.linspace(1, 0, fo)
    return x


def save(x, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", "-",
                    "-c:a", "libvorbis", "-q:a", "5", str(path)], input=x.astype(np.float32).tobytes(), check=True)


def play(path):
    if shutil.which("ffplay"):
        subprocess.run(["ffplay", "-v", "error", "-nodisp", "-autoexit", str(path)])


def credit(name):
    """Note own recordings in CREDITS.md (once per sound name)."""
    text = CREDITS.read_text() if CREDITS.exists() else "# Sound credits\n"
    marker = "## Recorded for this game"
    row = f"| `{name}*.ogg` | {USES.get(name, 'custom sound')} |"
    if f"| `{name}*.ogg` |" in text:
        return
    if marker not in text:
        text = text.rstrip() + f"\n\n{marker}\n\n| Game file(s) | Line |\n|---|---|\n"
    CREDITS.write_text(text.rstrip("\n") + "\n" + row + "\n")


def main():
    ap = argparse.ArgumentParser(description="Record a sound into Swoopin.")
    ap.add_argument("name", nargs="?", help="sound name, e.g. threat or shoo")
    ap.add_argument("--seconds", type=float, default=3.0, help="how long to record (default 3)")
    ap.add_argument("--replace", action="store_true", help="delete earlier takes of this name first")
    ap.add_argument("--device", default="default", help="PulseAudio source (default: your default mic)")
    ap.add_argument("--list", action="store_true", help="show the sound names the game uses")
    args = ap.parse_args()

    if args.list or not args.name:
        print("Sound names (record several takes of one to get random variants):\n")
        for k, v in USES.items():
            n = len(list(SOUND_DIR.glob(f"{k}*.ogg")))
            print(f"  {k:9s} {n} take(s)   {v}")
        return
    name = args.name.strip().lower()
    if not name.isalpha():
        sys.exit("Use letters only for the name (takes are numbered automatically).")
    if args.replace:
        for old in SOUND_DIR.glob(f"{name}[0-9]*.ogg"):
            old.unlink()
        if (SOUND_DIR / f"{name}.ogg").exists():
            (SOUND_DIR / f"{name}.ogg").unlink()
    n = 0
    while (SOUND_DIR / f"{name}{n}.ogg").exists():
        n += 1
    out = SOUND_DIR / f"{name}{n}.ogg"

    print(f"Recording '{name}' -> {out.name}  ({USES.get(name, 'custom sound')})")
    for c in ("3", "2", "1"):
        print(f"  {c}...", flush=True)
        time.sleep(0.7)
    print("  GO!")
    raw = record(args.seconds, args.device)
    try:
        x = clean(load(raw))
    finally:
        raw.unlink(missing_ok=True)
    save(x, out)
    credit(name)
    print(f"Saved {out}  ({len(x) / RATE:.2f}s). Playing it back...")
    play(out)
    print(f"Don't like it? Delete {out.name} or run again with --replace.")


if __name__ == "__main__":
    main()

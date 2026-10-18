# PyInstaller spec for Swoopin.  Build from the repo root:
#     pyinstaller packaging/swoopin.spec
# Windows / Linux: one self-contained file in dist/.
# macOS: dist/Swoopin.app.
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT)],
    datas=[(str(ROOT / "swoopin" / "sounds"), "swoopin/sounds")],
    excludes=["tkinter", "swoopin.record"],  # the recorder is a dev tool (needs ffmpeg + a mic)
    noarchive=False,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Swoopin", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="Swoopin")
    app = BUNDLE(coll, name="Swoopin.app", bundle_identifier="io.github.wufle.swoopin",
                 info_plist={"NSHighResolutionCapable": True})
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="Swoopin" if sys.platform == "win32" else "swoopin",
              console=False, upx=False)

#!/usr/bin/env python3
"""Packs a PS Vita .vpk from the Godot Vita port's template and our game.pck.

This does exactly what the Vita port's editor exporter does
(platform/vita/export/export.cpp in SonicMastr/godot-vita), so the VPK can be
built in CI with stock Godot 3.5.x:

  vita_release.zip (eboot.bin + GPU modules + livearea template.xml)
  + game_data/game.pck
  + sce_sys/param.sfo   (same layout as the port's vita-mksfoex)
  + sce_sys/icon0.png, pic0.png, livearea/contents/bg.png, startup.png

    python3 tools/make_vpk.py --template vita_release.zip --pck build/game.pck \
        --out build/MyGame.vpk --title "My Game" --title-id MYGM00001 \
        --version 00.40 --art vita
"""
import argparse
import os
import struct
import sys
import zipfile

PSF_TYPE_STR = 2
PSF_TYPE_VAL = 4


def make_sfo(title: str, title_id: str, version: str, parental: int = 1) -> bytes:
    if len(title_id) != 9:
        sys.exit("TITLE_ID must be 9 characters (e.g. BALR00001)")
    if len(version) != 5 or version[2] != ".":
        sys.exit("version must look like 01.00")
    # name, type, value (or max size for strings), data  - same order and
    # defaults as vita-mksfoex in the Godot Vita port
    entries = [
        ("APP_VER", PSF_TYPE_STR, 0, "00.00"),
        ("ATTRIBUTE", PSF_TYPE_VAL, 0x8000, None),
        ("ATTRIBUTE2", PSF_TYPE_VAL, 12, None),
        ("ATTRIBUTE_MINOR", PSF_TYPE_VAL, 0x10, None),
        ("BOOT_FILE", PSF_TYPE_STR, 32, ""),
        ("CATEGORY", PSF_TYPE_STR, 0, "gd"),
        ("CONTENT_ID", PSF_TYPE_STR, 48, ""),
        ("EBOOT_APP_MEMSIZE", PSF_TYPE_VAL, 0, None),
        ("EBOOT_ATTRIBUTE", PSF_TYPE_VAL, 0, None),
        ("EBOOT_PHY_MEMSIZE", PSF_TYPE_VAL, 0, None),
        ("LAREA_TYPE", PSF_TYPE_VAL, 0, None),
        ("NP_COMMUNICATION_ID", PSF_TYPE_STR, 16, ""),
        ("PARENTAL_LEVEL", PSF_TYPE_VAL, max(0, min(11, parental)), None),
        ("PSP2_DISP_VER", PSF_TYPE_STR, 0, "00.000"),
        ("PSP2_SYSTEM_VER", PSF_TYPE_VAL, 0, None),
        ("STITLE", PSF_TYPE_STR, 52, title),
        ("TITLE", PSF_TYPE_STR, 0x80, title),
        ("TITLE_ID", PSF_TYPE_STR, 0, title_id.upper()),
        ("VERSION", PSF_TYPE_STR, 0, version),
    ]
    head = b""
    keys = b""
    data = b""
    for name, typ, value, s in entries:
        nameofs = len(keys)
        dataofs = len(data)
        keys += name.encode("ascii") + b"\0"
        if typ == PSF_TYPE_VAL:
            valsize = totalsize = 4
            data += struct.pack("<I", value)
        else:
            raw = (s or "").encode("utf-8") + b"\0"
            valsize = len(raw)
            totalsize = value if value else (valsize + 3) & ~3
            if valsize > totalsize:
                sys.exit("%s is too long" % name)
            data += raw + b"\0" * (totalsize - valsize)
        head += struct.pack("<HBBIII", nameofs, 4, typ, valsize, totalsize, dataofs)
    keys += b"\0" * ((4 - len(keys) % 4) % 4)
    keyofs = 20 + len(head)
    valofs = keyofs + len(keys)
    header = struct.pack("<IIIII", 0x46535000, 0x00000101, keyofs, valofs, len(entries))
    return header + head + keys + data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, help="vita_release.zip from the Godot Vita port")
    ap.add_argument("--pck", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Godot Game")
    ap.add_argument("--title-id", default="GODT00001")
    ap.add_argument("--version", default="01.00")
    ap.add_argument("--art", default="vita")
    a = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    art = {
        "sce_sys/icon0.png": "icon0.png",
        "sce_sys/pic0.png": "pic0.png",
        "sce_sys/livearea/contents/bg.png": "bg.png",
        "sce_sys/livearea/contents/startup.png": "startup.png",
    }
    with zipfile.ZipFile(a.template) as tz, zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as vz:
        for info in tz.infolist():
            if info.filename.endswith("/") or info.filename in art:
                continue
            vz.writestr(info.filename, tz.read(info.filename))
        vz.write(a.pck, "game_data/game.pck")
        vz.writestr("sce_sys/param.sfo", make_sfo(a.title, a.title_id, a.version))
        for dst, src in art.items():
            p = os.path.join(a.art, src)
            if os.path.exists(p):
                vz.write(p, dst)
            else:
                print("warning: missing art", p)
    print("wrote", a.out, os.path.getsize(a.out), "bytes")


if __name__ == "__main__":
    main()

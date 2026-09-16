"""Replace the primary Windows icon embedded in a PE executable.

Uses only Python stdlib + Win32 resource APIs, so the Softsembly build does not
need Visual Studio, Node, Resource Hacker, or another third-party icon patcher.
"""
from __future__ import annotations

import argparse
import ctypes
import struct
import sys
from pathlib import Path
from ctypes import wintypes

RT_ICON = 3
RT_GROUP_ICON = 14
LOAD_LIBRARY_AS_DATAFILE = 0x00000002
LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x00000020

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

BeginUpdateResourceW = kernel32.BeginUpdateResourceW
BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
BeginUpdateResourceW.restype = wintypes.HANDLE

UpdateResourceW = kernel32.UpdateResourceW
UpdateResourceW.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.WORD,
    wintypes.LPVOID,
    wintypes.DWORD,
]
UpdateResourceW.restype = wintypes.BOOL

EndUpdateResourceW = kernel32.EndUpdateResourceW
EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]
EndUpdateResourceW.restype = wintypes.BOOL


def MAKEINTRESOURCE(value: int):
    return ctypes.cast(ctypes.c_void_p(value), wintypes.LPCWSTR)


def win_error(message: str) -> OSError:
    return OSError(ctypes.get_last_error(), message)


def parse_ico(path: Path):
    raw = path.read_bytes()
    if len(raw) < 6:
        raise ValueError("ICO file is too short")
    reserved, icon_type, count = struct.unpack_from("<HHH", raw, 0)
    if reserved != 0 or icon_type != 1 or count < 1:
        raise ValueError("Not a valid Windows icon file")

    entries = []
    offset = 6
    for index in range(count):
        if offset + 16 > len(raw):
            raise ValueError("ICO directory is truncated")
        width, height, color_count, reserved_b, planes, bit_count, size, image_offset = struct.unpack_from(
            "<BBBBHHII", raw, offset
        )
        image = raw[image_offset : image_offset + size]
        if len(image) != size:
            raise ValueError("ICO image data is truncated")
        entries.append(
            {
                "width": width,
                "height": height,
                "color_count": color_count,
                "reserved": reserved_b,
                "planes": planes,
                "bit_count": bit_count,
                "size": size,
                "image": image,
            }
        )
        offset += 16
    return entries


def patch_icon(exe_path: Path, ico_path: Path):
    entries = parse_ico(ico_path)

    # Start icon IDs at 1. ThonnyRunner's primary icon group is also ID 1.
    icon_ids = list(range(1, len(entries) + 1))

    # GRPICONDIR + GRPICONDIRENTRY[]
    group = bytearray(struct.pack("<HHH", 0, 1, len(entries)))
    for entry, icon_id in zip(entries, icon_ids):
        group.extend(
            struct.pack(
                "<BBBBHHIH",
                entry["width"],
                entry["height"],
                entry["color_count"],
                entry["reserved"],
                entry["planes"],
                entry["bit_count"],
                entry["size"],
                icon_id,
            )
        )

    handle = BeginUpdateResourceW(str(exe_path), False)
    if not handle:
        raise win_error(f"Could not open {exe_path} for resource updates")

    committed = False
    try:
        for entry, icon_id in zip(entries, icon_ids):
            data = ctypes.create_string_buffer(entry["image"])
            ok = UpdateResourceW(
                handle,
                MAKEINTRESOURCE(RT_ICON),
                MAKEINTRESOURCE(icon_id),
                0x0409,
                data,
                len(entry["image"]),
            )
            if not ok:
                raise win_error(f"Could not write icon resource {icon_id}")

        group_data = ctypes.create_string_buffer(bytes(group))
        ok = UpdateResourceW(
            handle,
            MAKEINTRESOURCE(RT_GROUP_ICON),
            MAKEINTRESOURCE(1),
            0x0409,
            group_data,
            len(group),
        )
        if not ok:
            raise win_error("Could not write icon group resource")

        if not EndUpdateResourceW(handle, False):
            raise win_error("Could not commit executable resource changes")
        committed = True
    finally:
        if not committed:
            EndUpdateResourceW(handle, True)


if __name__ == "__main__":
    if sys.platform != "win32":
        raise SystemExit("patch_exe_icon.py must run on Windows")

    parser = argparse.ArgumentParser()
    parser.add_argument("exe", type=Path)
    parser.add_argument("ico", type=Path)
    args = parser.parse_args()

    patch_icon(args.exe.resolve(), args.ico.resolve())
    print(f"Embedded Softsembly icon into {args.exe}")

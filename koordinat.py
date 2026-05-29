"""
import_koordinat.py
───────────────────
Update graphBuilder.py dengan koordinat dari koordinat_template.json.
Taruh file ini di folder yang sama dengan semua file lainnya.

Cara pakai:
    1. Isi koordinat_template.json dari Google Maps
    2. python import_koordinat.py   ← update graphBuilder.py
    3. python build_halte_manual.py ← generate halte.json
    4. python mainapp.py            ← jalankan GUI
"""

import json
import re

TEMPLATE = "koordinat_template.json"
BUILDER  = "graphBuilder.py"


def main():
    # Load template
    if not __import__("os").path.exists(TEMPLATE):
        print(f"❌ {TEMPLATE} tidak ditemukan!")
        return

    with open(TEMPLATE, encoding="utf-8") as f:
        data = json.load(f)

    # Kumpulkan semua halte yang sudah diisi
    filled = []
    for key in ["koridor_1", "koridor_2A", "koridor_2B"]:
        for h in data.get(key, []):
            if h["lat"] is not None and h["lon"] is not None:
                filled.append(h)

    empty = sum(
        1 for key in ["koridor_1", "koridor_2A", "koridor_2B"]
        for h in data.get(key, [])
        if h["lat"] is None
    )

    print(f"  ✅ Koordinat terisi : {len(filled)}")
    print(f"  ⏳ Belum diisi      : {empty}")

    if not filled:
        print("\n❌ Belum ada koordinat yang diisi di template!")
        return

    # Baca graphBuilder.py
    with open(BUILDER, encoding="utf-8") as f:
        content = f.read()

    updated = 0
    added   = []

    for h in filled:
        nama = h["nama"]
        lat  = h["lat"]
        lon  = h["lon"]

        # Coba update yang sudah ada
        pattern     = rf'("{re.escape(nama)}":\s*)\([^)]+\)'
        replacement = rf'\g<1>({lat}, {lon})'
        new_content, n = re.subn(pattern, replacement, content)

        if n > 0:
            content = new_content
            updated += 1
            print(f"  ✅ Updated : {nama:35s} → ({lat}, {lon})")
        else:
            # Belum ada di dict, catat untuk ditambah
            added.append((nama, lat, lon))
            print(f"  ➕ Baru    : {nama:35s} → ({lat}, {lon})")

    # Tambahkan entry baru ke KOORDINAT_MANUAL
    if added:
        new_entries = ""
        for nama, lat, lon in added:
            padding    = max(1, 36 - len(nama))
            new_entries += f'    "{nama}":{" " * padding}({lat},  {lon}),\n'

        # Sisipkan sebelum baris penutup dict KOORDINAT_MANUAL
        content = content.replace(
            "}\n\n\n# ─────────────────────────────────────────────────────────────────\n#  TARIF",
            new_entries + "}\n\n\n# ─────────────────────────────────────────────────────────────────\n#  TARIF"
        )

    # Simpan
    with open(BUILDER, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n{'='*50}")
    print(f"  graphBuilder.py diupdate!")
    print(f"  Updated : {updated} koordinat")
    print(f"  Ditambah: {len(added)} koordinat baru")
    print(f"{'='*50}")
    print(f"\n  Selanjutnya: python build_halte_manual.py")


if __name__ == "__main__":
    main()
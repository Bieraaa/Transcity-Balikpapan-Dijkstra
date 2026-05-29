"""
build_halte_manual.py
─────────────────────
Generate output/halte.json dari koordinat di koordinat_template.json.
Taruh file ini di folder yang sama dengan semua file lainnya.

Cara pakai:
    1. Isi koordinat_template.json dari Google Maps
    2. python build_halte_manual.py
    3. python mainapp.py
"""

import json
import os

from Datarute import (
    HALTE_KORIDOR_1, HALTE_KORIDOR_2A, HALTE_KORIDOR_2B,
)

TEMPLATE   = "koordinat_template.json"
OUTPUT_DIR = "output"


def main():
    # Load template koordinat
    if not os.path.exists(TEMPLATE):
        print(f"❌ File {TEMPLATE} tidak ditemukan!")
        return

    with open(TEMPLATE, encoding="utf-8") as f:
        tmpl = json.load(f)

    # Buat lookup: nama → (lat, lon)
    koordinat: dict[str, tuple] = {}
    for key in ["koridor_1", "koridor_2A", "koridor_2B"]:
        for h in tmpl.get(key, []):
            if h["lat"] is not None and h["lon"] is not None:
                koordinat[h["nama"]] = (h["lat"], h["lon"])

    print(f"  📍 Koordinat terisi: {len(koordinat)} halte")

    # Build halte.json
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    semua   = []
    counter = 1

    for koridor, halte_list in [
        ("1",  HALTE_KORIDOR_1),
        ("2A", HALTE_KORIDOR_2A),
        ("2B", HALTE_KORIDOR_2B),
    ]:
        for urutan, (nama, _) in enumerate(halte_list, 1):
            lat, lon = koordinat.get(nama, (None, None))
            semua.append({
                "id":      f"H{counter:03d}",
                "nama":    nama,
                "koridor": koridor,
                "urutan":  urutan,
                "lat":     lat,
                "lon":     lon,
                "status":  "found" if lat is not None else "not_found",
            })
            counter += 1

    path = os.path.join(OUTPUT_DIR, "halte.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(semua, f, ensure_ascii=False, indent=2)

    # Ringkasan
    found     = [h for h in semua if h["status"] == "found"]
    not_found = [h for h in semua if h["status"] == "not_found"]

    print(f"\n{'='*50}")
    print(f"  ✅ halte.json dibuat : {len(semua)} total halte")
    print(f"  📍 Ada koordinat     : {len(found)}")
    print(f"  ❌ Belum ada         : {len(not_found)}")
    if not_found:
        print(f"\n  Halte yang masih kosong (isi di template):")
        for h in not_found:
            print(f"    [{h['koridor']}] {h['nama']}")
    print(f"{'='*50}")
    print(f"  Tersimpan: {path}")
    print(f"\n  Selanjutnya: python mainapp.py")


if __name__ == "__main__":
    main()
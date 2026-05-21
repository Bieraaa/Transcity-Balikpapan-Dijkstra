import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Datarute.Halte_raw import HALTE_KORIDOR_1, HALTE_KORIDOR_2A, HALTE_KORIDOR_2B, BOBOT_KORIDOR, WAKTU_TRANSIT
from Djikstra.geocoder import cari_koordinat
from Djikstra.graphBuilder import build_graph

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def proses_koridor(label: str, halte_list: list) -> list:
    total = len(halte_list)
    print(f"\n{'═'*55}")
    print(f"  KORIDOR {label}  ({total} halte)")
    print(f"{'═'*55}")

    hasil = []
    for i, (nama, queries) in enumerate(halte_list, 1):
        print(f"\n  [{i:02d}/{total}] {nama}")
        data = cari_koordinat(nama, queries)
        data.update({"koridor": label, "urutan": i})
        hasil.append(data)
    return hasil


def simpan_output(semua: list):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Buat halte.json dengan ID urut
    halte_json = [
        {
            "id": f"H{i:03d}",
            "nama": h["nama"],
            "koridor": h["koridor"],
            "urutan": h["urutan"],
            "lat": h["lat"],
            "lon": h["lon"],
            "status": h["status"],
        }
        for i, h in enumerate(semua, 1)
    ]

    # Build graph & edge list
    graph = build_graph(halte_json, BOBOT_KORIDOR, WAKTU_TRANSIT)

    # Flatten graph ke edge list untuk rute.json
    seen = set()
    edges = []
    for dari, neighbors in graph.items():
        for n in neighbors:
            key = tuple(sorted([dari, n["ke"]])) + (n["koridor"],)
            if key not in seen:
                seen.add(key)
                edges.append({"dari": dari, **n})

    rute_json = {
        "total_edges": len(edges) * 2,
        "total_transit": sum(1 for e in edges if e["koridor"] == "TRANSIT"),
        "edges": edges,
    }

    # Simpan file
    with open(f"{OUTPUT_DIR}/halte.json", "w", encoding="utf-8") as f:
        json.dump(halte_json, f, ensure_ascii=False, indent=2)

    with open(f"{OUTPUT_DIR}/rute.json", "w", encoding="utf-8") as f:
        json.dump(rute_json, f, ensure_ascii=False, indent=2)

    not_found = [h for h in semua if h["status"] == "not_found"]
    if not_found:
        with open(f"{OUTPUT_DIR}/not_found.json", "w", encoding="utf-8") as f:
            json.dump(not_found, f, ensure_ascii=False, indent=2)

    # Ringkasan
    found_n = sum(1 for h in semua if h["status"] == "found")
    total   = len(semua)
    print(f"\n{'═'*55}")
    print(f"  SELESAI!")
    print(f"{'═'*55}")
    print(f"  ✅ Koordinat ditemukan : {found_n}/{total} halte")
    print(f"  ❌ Perlu input manual  : {len(not_found)} halte")
    print(f"  🔗 Total edge graph    : {len(edges) * 2}")
    print(f"  📁 Output di           : output/")
    print(f"\n  File:")
    print(f"    📄 halte.json      ← data halte + koordinat")
    print(f"    📄 rute.json       ← graph untuk Dijkstra")
    if not_found:
        print(f"    📄 not_found.json  ← isi lat/lon manual")
    print(f"{'═'*55}\n")


def main():
    total = len(HALTE_KORIDOR_1) + len(HALTE_KORIDOR_2A) + len(HALTE_KORIDOR_2B)
    print("=" * 55)
    print("  🚌  BACITRA HALTE GEOCODER")
    print("  Nominatim OpenStreetMap — Gratis, Tanpa API Key")
    print("=" * 55)
    print(f"\n  Total halte  : {total}")
    print(f"  Est. durasi  : ~{total * 1.5 / 60:.0f} menit")
    print(f"\n  Tekan Enter untuk mulai, Ctrl+C untuk batal.")
    input()

    semua = []
    semua += proses_koridor("1",  HALTE_KORIDOR_1)
    semua += proses_koridor("2A", HALTE_KORIDOR_2A)
    semua += proses_koridor("2B", HALTE_KORIDOR_2B)
    simpan_output(semua)


if __name__ == "__main__":
    main()
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Djikstra.graphBuilder import load_graph_dari_file
from Djikstra.Djikstra import cari_rute


HALTE_JSON = os.path.join(os.path.dirname(__file__), "..", "output", "halte.json")


def tampilkan_hasil(result):
    print("\n" + "═" * 50)
    if not result.ditemukan:
        print(f"  ❌ Rute tidak ditemukan")
        print(f"  {result.pesan}")
        return

    print(f"  🚌 RUTE DITEMUKAN")
    print("═" * 50)
    print(f"  Dari    : {result.nama_asal}")
    print(f"  Ke      : {result.nama_tujuan}")
    print(f"  Waktu   : {result.total_waktu} menit")
    print(f"  Halte   : {result.jumlah_halte} halte")
    print(f"  Koridor : {' + '.join(result.koridor_dipakai)}")

    if result.transit:
        print(f"\n  🔄 Transit ({len(result.transit)}x):")
        for t in result.transit:
            print(f"     ▸ Di {t.di_halte_nama}")
            print(f"       Koridor {t.dari_koridor} → Koridor {t.ke_koridor}")

    print(f"\n  📍 Urutan Halte:")
    for i, nama in enumerate(result.rute_nama):
        prefix = "  🟢" if i == 0 else ("  🔴" if i == len(result.rute_nama) - 1 else "   ●")
        print(f"  {prefix} {i+1:02d}. {nama}")
    print("═" * 50)


def pilih_halte(halte_list: list, prompt: str) -> str:
    print(f"\n  {prompt}")
    print(f"  (Ketik sebagian nama, case-insensitive)")
    keyword = input("  → ").strip().lower()

    cocok = [h for h in halte_list if keyword in h["nama"].lower()]

    if not cocok:
        print("  Tidak ada halte yang cocok.")
        return pilih_halte(halte_list, prompt)

    if len(cocok) == 1:
        print(f"  ✅ Dipilih: {cocok[0]['nama']} [{cocok[0]['id']}]")
        return cocok[0]["id"]

    print(f"\n  Ditemukan {len(cocok)} halte:")
    for i, h in enumerate(cocok, 1):
        print(f"    {i}. [{h['koridor']}] {h['nama']} ({h['id']})")
    idx = input(f"  Pilih nomor (1-{len(cocok)}): ").strip()
    try:
        return cocok[int(idx) - 1]["id"]
    except (ValueError, IndexError):
        print("  Input tidak valid.")
        return pilih_halte(halte_list, prompt)


def main():
    if not os.path.exists(HALTE_JSON):
        print("❌ File output/halte.json belum ada.")
        print("   Jalankan dulu: python scripts/run_geocoder.py")
        return

    print("=" * 50)
    print("  🚌  BACITRA ROUTE TESTER (CLI)")
    print("=" * 50)

    graph, halte_list = load_graph_dari_file(HALTE_JSON)
    print(f"\n  Graph dimuat: {len(halte_list)} halte, {sum(len(v) for v in graph.values())} edge")

    while True:
        id_asal    = pilih_halte(halte_list, "Halte ASAL:")
        id_tujuan  = pilih_halte(halte_list, "Halte TUJUAN:")

        result = cari_rute(graph, halte_list, id_asal, id_tujuan)
        tampilkan_hasil(result)

        lagi = input("\n  Cari rute lain? (y/n): ").strip().lower()
        if lagi != "y":
            break

    print("\n  Sampai jumpa! 🚌\n")


if __name__ == "__main__":
    main()
"""
test_Djikstra.py
────────────────
CLI tester untuk pencarian rute Bacitra.
Jalankan dari root folder proyek:
    python test_Djikstra.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from Djikstra.graphBuilder import load_graph_dari_file
from Djikstra.Djikstra import cari_rute

HALTE_JSON = os.path.join(os.path.dirname(__file__), "output", "halte.json")

WARNA_KORIDOR = {"1": "\033[92m", "2A": "\033[95m", "2B": "\033[96m"}
RST  = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
RED  = "\033[91m"
GRN  = "\033[92m"
YEL  = "\033[93m"
BLU  = "\033[94m"
CYN  = "\033[96m"


def garis(char="═", lebar=56):
    print(char * lebar)


def tampilkan_hasil(result, km_hint: float = 0.0):
    print()
    garis()

    if not result.ditemukan:
        print(f"  {RED}❌  Rute tidak ditemukan{RST}")
        print(f"  {DIM}{result.pesan}{RST}")
        garis()
        return

    print(f"  {BOLD}{GRN}✅  RUTE DITEMUKAN{RST}")
    garis()
    print(f"  {BOLD}Dari   :{RST} {result.nama_asal}")
    print(f"  {BOLD}Ke     :{RST} {result.nama_tujuan}")
    print()

    # ── Ringkasan ─────────────────────────────────────────────
    print(f"  {YEL}⏱  Waktu tempuh  :{RST}  {result.total_waktu} menit")
    print(f"  {YEL}🚏 Jumlah halte  :{RST}  {result.jumlah_halte} halte")
    kor_str = "  →  ".join(
        f"{WARNA_KORIDOR.get(k, '')}Kor.{k}{RST}" for k in result.koridor_dipakai
    )
    print(f"  {YEL}🛤  Koridor       :{RST}  {kor_str}")

    transit_str = (f"{len(result.transit)}x transit"
                   if result.transit else "Tidak ada (1 koridor langsung)")
    print(f"  {YEL}🔄 Transit       :{RST}  {transit_str}")
    print(f"  {YEL}💰 Biaya         :{RST}  Rp {result.total_biaya:,}  ({result.tipe_penumpang})")
    if result.detail_biaya:
        print(f"     {DIM}Rincian : {result.detail_biaya}{RST}")

    # ── Titik transit ─────────────────────────────────────────
    if result.transit:
        print()
        print(f"  {BLU}{BOLD}🔵  Titik Transit ({len(result.transit)}x):{RST}")
        for i, t in enumerate(result.transit, 1):
            print(f"  {BLU}  {i}. {t.di_halte_nama}{RST}")
            print(f"     Koridor {t.dari_koridor}  →  Koridor {t.ke_koridor}")

    # ── Urutan halte ──────────────────────────────────────────
    print()
    print(f"  {BOLD}📍  Urutan Halte yang Dilewati:{RST}")

    transit_ids = {t.di_halte_id for t in result.transit}
    kor_aktif   = None

    # Map id → koridor
    from Djikstra.graphBuilder import load_graph_dari_file as _lgf
    import json
    with open(HALTE_JSON, encoding="utf-8") as f:
        halte_map = {h["id"]: h for h in json.load(f)}

    for i, (hid, nama) in enumerate(zip(result.rute_id, result.rute_nama)):
        kor = halte_map.get(hid, {}).get("koridor", "?")
        wk  = WARNA_KORIDOR.get(kor, "")

        if kor != kor_aktif:
            if kor_aktif is not None:
                print()
            print(f"  {wk}{BOLD}─── Koridor {kor} ───{RST}")
            kor_aktif = kor

        if   hid == result.rute_id[0]:   ikon = f"{GRN}🟢{RST}"
        elif hid == result.rute_id[-1]:  ikon = f"{RED}🔴{RST}"
        elif hid in transit_ids:         ikon = f"{BLU}🔵{RST}"
        else:                            ikon = f"{DIM} ○{RST}"

        print(f"  {ikon}  {i+1:02d}. {wk}{nama}{RST}")

    print()
    garis()


def pilih_halte(halte_list: list, prompt: str) -> str:
    print(f"\n  {BOLD}{prompt}{RST}")
    print(f"  {DIM}(Ketik sebagian nama halte, tidak perlu huruf kapital){RST}")
    keyword = input(f"  → ").strip().lower()

    cocok = [h for h in halte_list if keyword in h["nama"].lower()]

    if not cocok:
        print(f"  {RED}Tidak ada halte yang cocok. Coba kata lain.{RST}")
        return pilih_halte(halte_list, prompt)

    if len(cocok) == 1:
        print(f"  {GRN}✅ Dipilih: {cocok[0]['nama']} "
              f"[Kor.{cocok[0]['koridor']}] ({cocok[0]['id']}){RST}")
        return cocok[0]["id"]

    print(f"\n  Ditemukan {len(cocok)} halte dengan nama tersebut:")
    for i, h in enumerate(cocok, 1):
        wk = WARNA_KORIDOR.get(h["koridor"], "")
        print(f"    {i}. {wk}[Kor.{h['koridor']}]{RST}  {h['nama']}  {DIM}({h['id']}){RST}")

    idx = input(f"  Pilih nomor (1-{len(cocok)}): ").strip()
    try:
        return cocok[int(idx) - 1]["id"]
    except (ValueError, IndexError):
        print(f"  {RED}Input tidak valid.{RST}")
        return pilih_halte(halte_list, prompt)


def main():
    if not os.path.exists(HALTE_JSON):
        print(f"{RED}❌ File output/halte.json tidak ditemukan!{RST}")
        print(f"   Jalankan dulu: python BuildHalte.py")
        return

    print()
    garis("═")
    print(f"  {BOLD}🚌  BACITRA ROUTE TESTER — CLI{RST}")
    print(f"  {DIM}Balikpapan City Trans — Dijkstra Pathfinder{RST}")
    garis("═")

    graph, halte_list = load_graph_dari_file(HALTE_JSON)
    n_edge = sum(len(v) for v in graph.values())
    print(f"\n  {GRN}✅ Graf dimuat:{RST} {len(halte_list)} halte | {n_edge} edge")

    while True:
        id_asal   = pilih_halte(halte_list, "Halte ASAL:")
        id_tujuan = pilih_halte(halte_list, "Halte TUJUAN:")

        pelajar_input = input(
            f"\n  {DIM}Tarif pelajar? (y/n, default=n): {RST}"
        ).strip().lower()
        pelajar = pelajar_input == "y"

        result = cari_rute(graph, halte_list, id_asal, id_tujuan, pelajar)
        tampilkan_hasil(result)

        lagi = input(f"\n  {DIM}Cari rute lain? (y/n): {RST}").strip().lower()
        if lagi != "y":
            break

    print(f"\n  {GRN}Terima kasih! Selamat bepergian. 🚌{RST}\n")


if __name__ == "__main__":
    main()
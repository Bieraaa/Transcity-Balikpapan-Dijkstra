import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from Djikstra.graphBuilder import load_graph_dari_file
from Djikstra.Djikstra     import cari_rute

HALTE_JSON = os.path.join(os.path.dirname(__file__), "output", "halte.json")

# ANSI color
RST  = "\033[0m";  BOLD = "\033[1m";  DIM  = "\033[2m"
RED  = "\033[91m"; GRN  = "\033[92m"; YEL  = "\033[93m"
BLU  = "\033[94m"; CYN  = "\033[96m"
WARNA_KOR = {"1": GRN, "2A": "\033[95m", "2B": CYN}


def garis(char="═", n=58):
    print(char * n)


def tampilkan_hasil(result, halte_map: dict):
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

    # Peringatan rute memutar
    if result.pesan:
        print(f"  {YEL}{result.pesan}{RST}")
        print()

    # Ringkasan
    print(f"  {YEL}⏱  Waktu tempuh  :{RST}  {result.total_waktu} menit")
    print(f"  {YEL}📏 Jarak total   :{RST}  ~{result.total_km:.1f} km (estimasi)")
    print(f"  {YEL}🚏 Jumlah halte  :{RST}  {result.jumlah_halte} halte")

    kor_str = "  →  ".join(
        f"{WARNA_KOR.get(k,'')}Kor.{k}{RST}" for k in result.koridor_dipakai
    )
    print(f"  {YEL}🛤  Koridor       :{RST}  {kor_str}")

    tr_str = (f"{len(result.transit)}x transit"
            if result.transit else "Tidak ada (1 koridor langsung)")
    print(f"  {YEL}🔄 Transit       :{RST}  {tr_str}")
    print(f"  {YEL}💰 Biaya         :{RST}  Rp {result.total_biaya:,}  "
        f"({result.tipe_penumpang})")
    if result.detail_biaya:
        print(f"     {DIM}Rincian : {result.detail_biaya}{RST}")

    # Titik transit
    if result.transit:
        print()
        print(f"  {BLU}{BOLD}🔵  Titik Transit ({len(result.transit)}x):{RST}")
        for i, t in enumerate(result.transit, 1):
            print(f"  {BLU}  {i}. {t.di_halte_nama}{RST}")
            print(f"     Kor.{t.dari_koridor}  →  Kor.{t.ke_koridor}")

    # Jarak per segmen (ringkas: maks 8 segmen pertama)
    if result.segmen_km:
        print()
        print(f"  {BOLD}📏  Jarak Antar Halte (km):{RST}")
        kumulatif = 0.0
        tampil    = result.segmen_km[:8]
        for s in tampil:
            kumulatif += s["km"]
            print(f"    {DIM}→ {s['ke']:35s}{RST}  "
                f"{s['km']:5.2f} km  (kumulatif ~{kumulatif:.2f} km)")
        if len(result.segmen_km) > 8:
            print(f"    {DIM}... dan {len(result.segmen_km)-8} segmen lainnya{RST}")

    # Urutan halte per koridor
    print()
    print(f"  {BOLD}📍  Urutan Halte:{RST}")
    transit_ids = {t.di_halte_id for t in result.transit}
    kor_aktif   = None

    for i, (hid, nama) in enumerate(zip(result.rute_id, result.rute_nama)):
        kor = halte_map.get(hid, {}).get("koridor", "?")
        wk  = WARNA_KOR.get(kor, "")
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
    print(f"  {DIM}Ketik sebagian nama halte (tidak perlu huruf kapital){RST}")
    keyword = input("  → ").strip().lower()
    cocok   = [h for h in halte_list if keyword in h["nama"].lower()]

    if not cocok:
        print(f"  {RED}Tidak ada yang cocok. Coba kata lain.{RST}")
        return pilih_halte(halte_list, prompt)

    if len(cocok) == 1:
        h = cocok[0]
        print(f"  {GRN}✅ {h['nama']} [Kor.{h['koridor']}] ({h['id']}){RST}")
        return h["id"]

    print(f"\n  Ditemukan {len(cocok)} halte:")
    for i, h in enumerate(cocok, 1):
        wk = WARNA_KOR.get(h["koridor"], "")
        print(f"    {i}. {wk}[Kor.{h['koridor']}]{RST}  {h['nama']}  "
            f"{DIM}({h['id']}){RST}")

    idx = input(f"  Pilih nomor (1-{len(cocok)}): ").strip()
    try:
        return cocok[int(idx) - 1]["id"]
    except (ValueError, IndexError):
        print(f"  {RED}Input tidak valid.{RST}")
        return pilih_halte(halte_list, prompt)


def main():
    if not os.path.exists(HALTE_JSON):
        print(f"{RED}❌ File output/halte.json tidak ditemukan!{RST}")
        return

    print()
    garis()
    print(f"  {BOLD}🚌  BACITRA ROUTE TESTER — CLI{RST}")
    print(f"  {DIM}Balikpapan City Trans · Dijkstra Pathfinder{RST}")
    garis()

    graph, halte_list = load_graph_dari_file(HALTE_JSON)
    halte_map         = {h["id"]: h for h in halte_list}
    n_edge            = sum(len(v) for v in graph.values())
    print(f"\n  {GRN}✅ Graf:{RST} {len(halte_list)} halte | {n_edge} edge")

    while True:
        id_asal   = pilih_halte(halte_list, "Halte ASAL:")
        id_tujuan = pilih_halte(halte_list, "Halte TUJUAN:")

        pelajar = input(
            f"\n  {DIM}Tarif pelajar? (y/n, default n): {RST}"
        ).strip().lower() == "y"

        result = cari_rute(graph, halte_list, id_asal, id_tujuan, pelajar)
        tampilkan_hasil(result, halte_map)

        if input(f"\n  {DIM}Cari rute lain? (y/n): {RST}").strip().lower() != "y":
            break

    print(f"\n  {GRN}Sampai jumpa! 🚌{RST}\n")


if __name__ == "__main__":
    main()
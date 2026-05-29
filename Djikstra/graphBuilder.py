import json
from itertools import groupby


# =========================================
# KOORDINAT
# =========================================

KOORDINAT_MANUAL: dict[str, tuple[float, float]] = {
 
    # ══ KORIDOR 1 ══════════════════════════════════════════════
    # Pelabuhan Semayang → Bandara Sepinggan
    # Jalur: pesisir barat → pusat kota → selatan → Kariangau → Bandara
 
    "Pelabuhan Semayang":           (-1.2678,  116.8316),
    "Melawai":                      (-1.2712,  116.8278),
    "Lapangan Merdeka":             (-1.2691,  116.8296),
    "RS Pertamina":                 (-1.2650,  116.8290),
    "PNW":                          (-1.2620,  116.8310),
    "Banua Patra":                  (-1.2608,  116.8302),
    "Bank Indonesia":               (-1.2638,  116.8324),
    "SD Bhayangkari":               (-1.2655,  116.8341),
    "Kantor Pos":                   (-1.2669,  116.8358),
    "Pasar Klandasan":              (-1.2681,  116.8375),
    "Terminal Rasa":                (-1.2693,  116.8393),
    "Blauran":                      (-1.2705,  116.8412),
    "Gedung Parkir Klandasan":      (-1.2718,  116.8431),
    "Simpang Plaza Balikpapan B":   (-1.2731,  116.8451),
    "Simpang Plaza Balikpapan A":   (-1.2742,  116.8468),  # ← TRANSIT 2A & 2B
    "BCA":                          (-1.2758,  116.8489),
    "Bank Danamon":                 (-1.2771,  116.8507),
    "Bulog":                        (-1.2785,  116.8524),
    "Nuansa":                       (-1.2799,  116.8541),
    "Balikpapan Permai":            (-1.2813,  116.8558),  # ← TRANSIT 2A
    "Ace Hardware":                 (-1.2826,  116.8574),
    "Samsat Markoni":               (-1.2840,  116.8591),
    "DKK":                          (-1.2853,  116.8607),
    "Pasar Baru":                   (-1.2866,  116.8623),
    "Kehutanan":                    (-1.2879,  116.8640),
    "Benakatai":                    (-1.2891,  116.8656),
    "Al Ihsan":                     (-1.2904,  116.8672),
    "SDN 006":                      (-1.2917,  116.8688),
    "Mekar Sari":                   (-1.2930,  116.8704),  # ← TRANSIT 2A & 2B
    "Gunung Pasir":                 (-1.2943,  116.8720),
    "KPP Pratama Penajam":          (-1.2956,  116.8736),
    "Puskib":                       (-1.2969,  116.8751),
    "Pomal":                        (-1.2982,  116.8767),
    "SDN 001":                      (-1.2995,  116.8782),
    "Karang Jati":                  (-1.3007,  116.8797),
    "Muara Rapak":                  (-1.3020,  116.8812),
    "Ibnu Sina":                    (-1.3032,  116.8827),
    "Plaza Rapak":                  (-1.3044,  116.8842),
    "Strat":                        (-1.3056,  116.8857),
    "SMAN 2 Balikpapan":            (-1.3068,  116.8871),
    "Samsat Muara Rapak":           (-1.3080,  116.8885),
    "SMPN 3 Balikpapan":            (-1.3092,  116.8899),
    "Bengrah":                      (-1.2890,  116.9010),
    "Inpres 4":                     (-1.2870,  116.8990),
    "SMK Setia Budi":               (-1.2850,  116.8971),
    "Pulau Indah":                  (-1.2831,  116.8952),
    "Simpang Perumnas":             (-1.2812,  116.8933),
    "SD Kartika V-3":               (-1.2658,  116.8914),
    "Yon Zipur":                    (-1.2560,  116.8895),
    "Perintis":                     (-1.2472,  116.8876),
    "Perumahan Ramayana":           (-1.2384,  116.8856),
    "Pemotongan Hewan":             (-1.2296,  116.8836),
    "Graha Indah":                  (-1.2208,  116.8817),
    "Masjid Santalia":              (-1.2120,  116.8797),
    "Perum PGRI":                   (-1.2032,  116.8777),
    "PT. PAC":                      (-1.1944,  116.8757),
    "Perum Griya Kariangau":        (-1.1856,  116.8737),
    "Puskesmas Kariangau":          (-1.1768,  116.8717),
    "SMP 16":                       (-1.1680,  116.8697),
    "SD 020":                       (-1.1592,  116.8677),
    "PT Petrosea":                  (-1.1504,  116.8657),
    "Kelurahan Kariangau":          (-1.1416,  116.8637),
    "Pelabuhan Kariangau":          (-1.1328,  116.8617),
    "Bandara Sepinggan":            (-1.2682,  116.8939),
 
    # ══ KORIDOR 2A ═════════════════════════════════════════════
    # Terminal Batu Ampar → Plaza Balikpapan via MT. Haryono
    # Jalur: Terminal → Jl. Soekarno-Hatta → Jl. MT Haryono → Plaza
 
    "Terminal Batu Ampar":          (-1.2315,  116.8720),  # ← TRANSIT 2A & 2B
    "Sabulussalam":                 (-1.2340,  116.8752),
    "Simpang Batu Ampar":           (-1.2362,  116.8779),
    "Pasar Butun":                  (-1.2384,  116.8806),
    "Al Auliya":                    (-1.2406,  116.8833),
    "Pelangi Metro":                (-1.2428,  116.8860),
    "RSKD":                         (-1.2450,  116.8887),
    "Grand City":                   (-1.2472,  116.8914),
    "Hotel Her":                    (-1.2494,  116.8941),
    "Global Sport":                 (-1.2516,  116.8968),
    "Daun Village":                 (-1.2538,  116.8995),
    "RS Balikpapan Baru":           (-1.2560,  116.9022),
    "Living Plaza":                 (-1.2582,  116.9049),
    "Majesty":                      (-1.2604,  116.9076),
    "PLN MT Haryono":               (-1.2626,  116.9103),
    "Masjid Shahibussalam":         (-1.2648,  116.9130),
    "RS Siloam":                    (-1.2670,  116.9157),
    "Bukit Damai Indah":            (-1.2692,  116.9184),
    "Kelurahan Damai Baru":         (-1.2714,  116.9211),
    "Dukcapil":                     (-1.2736,  116.9238),
    "Beller":                       (-1.2758,  116.9265),
    "B-Connect":                    (-1.2780,  116.9292),
    "Kolam Mulawarman":             (-1.2802,  116.9319),
    "SDN 012":                      (-1.2824,  116.9346),
    "Kavling 8 Square":             (-1.2845,  116.9195),
    "Siaga":                        (-1.2855,  116.9050),
    # "Balikpapan Permai" sudah di Koridor 1
    # "Ace Hardware"      sudah di Koridor 1
    # "Samsat Markoni"    sudah di Koridor 1
    # "DKK"               sudah di Koridor 1
    # "Pasar Baru"        sudah di Koridor 1
    # "Simpang Plaza Balikpapan A" sudah di Koridor 1
 
    # ══ KORIDOR 2B ═════════════════════════════════════════════
    # Terminal Batu Ampar → Plaza Balikpapan via Rapak
    # Jalur: Terminal → Jl. Ahmad Yani → Rapak → Plaza
 
    "Pegadaian":                    (-1.2330,  116.8735),
    # "Samsat Muara Rapak" sudah di Koridor 1
    # "Plaza Rapak"        sudah di Koridor 1
    # "Ibnu Sina"          sudah di Koridor 1
    # "SMAN 2 Balikpapan"  sudah di Koridor 1
    # "Strat"              sudah di Koridor 1
    # "Muara Rapak"        sudah di Koridor 1
    # "Karang Jati"        sudah di Koridor 1
    # "SDN 001"            sudah di Koridor 1
    # "Pomal"              sudah di Koridor 1
    # "Puskib"             sudah di Koridor 1
    # "KPP Pratama Penajam" sudah di Koridor 1
    # "Gunung Pasir"       sudah di Koridor 1
    # "SDN 006"            sudah di Koridor 1
    # "Al Ihsan"           sudah di Koridor 1
    # "Mekar Sari"         sudah di Koridor 1
    # "Kehutanan"          sudah di Koridor 1
    # "Benakatai"          sudah di Koridor 1
    # "Simpang Plaza Balikpapan A" sudah di Koridor 1
}
# =========================================
# Tarif BUs
# =========================================

TARIF_PER_KORIDOR = 5000   # Rp 5.000 per koridor
TARIF_PELAJAR    = 2000    # Rp 2.000 per koridor (dengan kartu pelajar)

def hitung_biaya(koridor_dipakai: list[str], pelajar: bool = False) -> dict:
    """
    Hitung biaya perjalanan berdasarkan koridor yang dipakai.

    Aturan:
    - Setiap koridor unik yang dinaiki = 1 tiket
    - Misal pakai koridor 1 saja         → Rp 5.000
    - Misal transit dari 2A ke 1         → Rp 10.000
    - Pelajar dengan kartu               → Rp 2.000/koridor

    Returns:
        {"jumlah_tiket": int, "total_biaya": int, "detail": str}
    """
    jumlah_tiket = len([k for k in koridor_dipakai if k != "TRANSIT"])
    tarif = TARIF_PELAJAR if pelajar else TARIF_PER_KORIDOR
    total = jumlah_tiket * tarif

    detail_tiket = " + ".join(
        f"Kor.{k} (Rp {tarif:,})"
        for k in koridor_dipakai if k != "TRANSIT"
    )

    return {
        "jumlah_tiket": jumlah_tiket,
        "total_biaya":  total,
        "tarif_per_tiket": tarif,
        "detail":       detail_tiket,
        "tipe":         "Pelajar" if pelajar else "Umum",
    }

# =========================================
# Helper 
# =========================================
def _normalisasi_nama(nama: str) -> str:
    return nama.lower().strip()

def _tambah_edge(edges, dari, ke, waktu, koridor, **extra):
    base  = {"dari": dari, "ke": ke,   "waktu_menit": waktu, "koridor": koridor, **extra}
    balik = {"dari": ke,   "ke": dari, "waktu_menit": waktu, "koridor": koridor, **extra}
    edges.extend([base, balik])

def _patch_koordinat(halte_list: list) -> list:
    """
    Isi koordinat yang None dengan data hardcode KOORDINAT_MANUAL.
    Ini memastikan halte transit selalu punya koordinat
    sehingga edge transit terbentuk dan rute tidak putus.
    """
    patched = 0
    for h in halte_list:
        if h["lat"] is None and h["nama"] in KOORDINAT_MANUAL:
            lat, lon = KOORDINAT_MANUAL[h["nama"]]
            h["lat"] = lat
            h["lon"] = lon
            patched += 1
    if patched:
        print(f"  📍 Koordinat di-patch manual: {patched} halte")
    return halte_list

# =========================================
# Graph Halte Bis 
# =========================================

def build_graph(halte_list: list, bobot: dict, waktu_transit: int) -> dict:
    """
    Bangun adjacency list dari data halte.

    PERBAIKAN:
    - Koordinat None di-patch dulu dari KOORDINAT_MANUAL
    - Deteksi transit lebih robust dengan normalisasi nama
    """
    # Patch koordinat yang kosong dulu
    halte_list = _patch_koordinat(halte_list)
    edges = []

    # 1. Koneksi berurutan dalam koridor yang sama
    sorted_h = sorted(halte_list, key=lambda x: (x["koridor"], x["urutan"]))
    for koridor, grp in groupby(sorted_h, key=lambda x: x["koridor"]):
        halte_kor = list(grp)
        w = bobot.get(koridor, 3)
        for j in range(len(halte_kor) - 1):
            a, b = halte_kor[j], halte_kor[j + 1]
            if a["lat"] is not None and b["lat"] is not None:
                _tambah_edge(edges, a["id"], b["id"], w, koridor)

    # 2. Koneksi transit antar koridor (nama halte sama)
    nama_map: dict[str, list] = {}
    for h in halte_list:
        key = _normalisasi_nama(h["nama"])
        nama_map.setdefault(key, []).append(h)

    transit_count = 0
    for key, group in nama_map.items():
        pairs = [
            (group[i], group[j])
            for i in range(len(group))
            for j in range(i + 1, len(group))
            if group[i]["koridor"] != group[j]["koridor"]
        ]
        for a, b in pairs:
            if a["lat"] is not None and b["lat"] is not None:
                ket = f"Transit {a['koridor']} <-> {b['koridor']}"
                _tambah_edge(edges, a["id"], b["id"], waktu_transit, "TRANSIT",keterangan=ket)
                transit_count += 1

    print(f"  🔗 Total edge: {len(edges)} | Transit points: {transit_count}")

    # 3. Ubah ke adjacency list
    graph: dict[str, list] = {h["id"]: [] for h in halte_list}
    for e in edges:
        graph[e["dari"]].append({
            "ke":          e["ke"],
            "waktu_menit": e["waktu_menit"],
            "koridor":     e["koridor"],
        })
    return graph

def load_graph_dari_file(
    path_halte: str = "output/halte.json",
    bobot: dict | None = None,
    waktu_transit: int = 10,
) -> tuple[dict, list]:
    if bobot is None:
        bobot = {"1": 4, "2A": 2, "2B": 4}

    with open(path_halte, encoding="utf-8") as f:
        halte_list = json.load(f)

    graph = build_graph(halte_list, bobot, waktu_transit)
    return graph, halte_list
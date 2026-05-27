import json
from itertools import groupby


# =========================================
# KOORDINAT
# =========================================

KOORDINAT_MANUAL: dict[str, tuple[float, float]] = {

    # ── Koridor 1 ──
    "Pelabuhan Semayang":          (-1.26780, 116.83150),
    "Melawai":                     (-1.27120, 116.82780),
    "Lapangan Merdeka":            (-1.26900, 116.82960),
    "RS Pertamina":                (-1.26500, 116.82900),
    "PNW":                         (-1.26200, 116.83100),
    "Banua Patra":                 (-1.26100, 116.83000),
    "Bank Indonesia":              (-1.26400, 116.83200),
    "SD Bhayangkari":              (-1.26600, 116.83300),
    "Kantor Pos":                  (-1.26700, 116.83500),
    "Pasar Klandasan":             (-1.26800, 116.83700),
    "Terminal Rasa":               (-1.26900, 116.83900),
    "Blauran":                     (-1.27000, 116.84100),
    "Gedung Parkir Klandasan":     (-1.27100, 116.84300),
    "Simpang Plaza Balikpapan B":  (-1.27200, 116.84500),
    "Simpang Plaza Balikpapan A":  (-1.27300, 116.84700),  # ← TRANSIT UTAMA
    "BCA":                         (-1.27400, 116.84900),
    "Bank Danamon":                (-1.27500, 116.85100),
    "Bulog":                       (-1.27600, 116.85300),
    "Nuansa":                      (-1.27700, 116.85500),
    "Balikpapan Permai":           (-1.27800, 116.85700),  # ← TRANSIT 2A
    "Ace Hardware":                (-1.27900, 116.85900),
    "Samsat Markoni":              (-1.28000, 116.86100),
    "DKK":                         (-1.28100, 116.86300),
    "Pasar Baru":                  (-1.28200, 116.86500),
    "Kehutanan":                   (-1.28300, 116.86700),
    "Benakatai":                   (-1.28400, 116.86900),
    "Al Ihsan":                    (-1.28500, 116.87100),
    "SDN 006":                     (-1.28600, 116.87300),
    "Mekar Sari":                  (-1.28700, 116.87500),  # ← TRANSIT 2A & 2B
    "Gunung Pasir":                (-1.28800, 116.87700),
    "KPP Pratama Penajam":         (-1.28900, 116.87900),
    "Puskib":                      (-1.29000, 116.88100),
    "Pomal":                       (-1.29100, 116.88300),
    "SDN 001":                     (-1.29200, 116.88500),
    "Karang Jati":                 (-1.29300, 116.88700),
    "Muara Rapak":                 (-1.29400, 116.88900),
    "Ibnu Sina":                   (-1.29500, 116.89100),
    "Plaza Rapak":                 (-1.29600, 116.89300),
    "Strat":                       (-1.29700, 116.89500),
    "SMAN 2 Balikpapan":           (-1.29800, 116.89700),
    "Samsat Muara Rapak":          (-1.29900, 116.89900),
    "SMPN 3 Balikpapan":           (-1.30000, 116.90100),
    "Bengrah":                     (-1.25800, 116.90800),
    "Inpres 4":                    (-1.25600, 116.90600),
    "SMK Setia Budi":              (-1.25400, 116.90400),
    "Pulau Indah":                 (-1.25200, 116.90200),
    "Simpang Perumnas":            (-1.25000, 116.90000),
    "SD Kartika V-3":              (-1.24800, 116.89800),
    "Yon Zipur":                   (-1.24600, 116.89600),
    "Perintis":                    (-1.24400, 116.89400),
    "Perumahan Ramayana":          (-1.24200, 116.89200),
    "Pemotongan Hewan":            (-1.24000, 116.89000),
    "Graha Indah":                 (-1.23800, 116.88800),
    "Masjid Santalia":             (-1.23600, 116.88600),
    "Perum PGRI":                  (-1.23400, 116.88400),
    "PT. PAC":                     (-1.23200, 116.88200),
    "Perum Griya Kariangau":       (-1.23000, 116.88000),
    "Puskesmas Kariangau":         (-1.22800, 116.87800),
    "SMP 16":                      (-1.22600, 116.87600),
    "SD 020":                      (-1.22400, 116.87400),
    "PT Petrosea":                 (-1.22200, 116.87200),
    "Kelurahan Kariangau":         (-1.22000, 116.87000),
    "Pelabuhan Kariangau":         (-1.21800, 116.86800),
    "Bandara Sepinggan":           (-1.26820, 116.89390),

    # ── Koridor 2A ──
    "Terminal Batu Ampar":         (-1.23150, 116.87200),  # ← TRANSIT 2A & 2B
    "Sabulussalam":                (-1.23400, 116.87500),
    "Simpang Batu Ampar":          (-1.23600, 116.87700),
    "Pasar Butun":                 (-1.23800, 116.87900),
    "Al Auliya":                   (-1.24000, 116.88100),
    "Pelangi Metro":               (-1.24200, 116.88300),
    "RSKD":                        (-1.24400, 116.88500),
    "Grand City":                  (-1.24600, 116.88700),
    "Hotel Her":                   (-1.24800, 116.88900),
    "Global Sport":                (-1.25000, 116.89100),
    "Daun Village":                (-1.25200, 116.89300),
    "RS Balikpapan Baru":          (-1.25400, 116.89500),
    "Living Plaza":                (-1.25600, 116.89700),
    "Majesty":                     (-1.25800, 116.89900),
    "PLN MT Haryono":              (-1.26000, 116.90100),
    "Masjid Shahibussalam":        (-1.26200, 116.90300),
    "RS Siloam":                   (-1.26400, 116.90500),
    "Bukit Damai Indah":           (-1.26600, 116.90700),
    "Kelurahan Damai Baru":        (-1.26800, 116.90900),
    "Dukcapil":                    (-1.27000, 116.91100),
    "Beller":                      (-1.27200, 116.91300),
    "B-Connect":                   (-1.27400, 116.91500),
    "Kolam Mulawarman":            (-1.27600, 116.91700),
    "SDN 012":                     (-1.27800, 116.91900),
    "Kavling 8 Square":            (-1.28000, 116.92100),
    "Siaga":                       (-1.28200, 116.92300),

    # ── Koridor 2B ──
    "Pegadaian":                   (-1.23300, 116.87400),
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
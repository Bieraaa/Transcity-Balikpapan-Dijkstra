import json, math
from itertools import groupby

# ══════════════════════════════════════════════════════════════
# Bobot Waktu edge
# ══════════════════════════════════════════════════════════════

BOBOT_DEFAULT: dict[str, float] = {
    "1" :  1.5,  # 95 menit ÷ 63 edge
    "2A": 2.2,   # 70 menit ÷ 32 edge
    "2B": 3.7,   # 70 menit ÷ 19 edge
}

WAKTU_TRANSIT_DEFAULT = 10 # menit estimasi pindah bus di halte transit

# ══════════════════════════════════════════════════════════════
# Tarif
# ══════════════════════════════════════════════════════════════

TARIF_PER_KORIDOR = 5_000   # Rp 5.000 per koridor (umum)
TARIF_PELAJAR     = 2_000   # Rp 2.000 per koridor (pelajar)


def hitung_biaya(koridor_dipakai: list[str], pelajar: bool = False) -> dict:

    koridor_bersih = [k for k in koridor_dipakai if k != "TRANSIT"]
    jumlah         = len(koridor_bersih)
    tarif          = TARIF_PELAJAR if pelajar else TARIF_PER_KORIDOR
    total          = jumlah * tarif
    detail         = " + ".join(f"Kor.{k} (Rp {tarif:,})" for k in koridor_bersih)

    return {
        "jumlah_tiket":    jumlah,
        "total_biaya":     total,
        "tarif_per_tiket": tarif,
        "detail":          detail,
        "tipe":            "Pelajar" if pelajar else "Umum",
    }

# ══════════════════════════════════════════════════════════════
# HAVERSINE - JARAK DUA KOORDINAT (KM)
# ══════════════════════════════════════════════════════════════

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R  = 6371.0
    d1 = math.radians(lat2 - lat1)
    d2 = math.radians(lon2 - lon1)
    a  = (math.sin(d1 / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d2 / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

# ══════════════════════════════════════════════════════════════
# Helper internal
# ══════════════════════════════════════════════════════════════

def _norm(nama: str) -> str:
    return nama.lower().strip()


def _tambah_edge(edges: list, dari: str, ke: str,
                 waktu: int, koridor: str, **extra) -> None:
    """Tambahkan edge dua arah (undirected)."""
    base  = {"dari": dari, "ke": ke,   "waktu_menit": waktu, "koridor": koridor, **extra}
    balik = {"dari": ke,   "ke": dari, "waktu_menit": waktu, "koridor": koridor, **extra}
    edges.extend([base, balik])


# ══════════════════════════════════════════════════════════════
# Build graph
# ══════════════════════════════════════════════════════════════

def build_graph(halte_list: list, bobot: dict [str, float], waktu_transit: float) -> dict:
    edges: list[dict] = []

    # ── 1. Edge dalam koridor ──────────────────────────────────
    sorted_h = sorted(halte_list, key=lambda x: (x["koridor"], x["urutan"]))
    for koridor, grp in groupby(sorted_h, key=lambda x: x["koridor"]):
        halte_kor = list(grp)
        w = bobot.get(koridor, 2.0)
        for j in range(len(halte_kor) - 1):
            a, b = halte_kor[j], halte_kor[j + 1]
            # Edge dibuat tanpa syarat koordinat
            _tambah_edge(edges, a["id"], b["id"], w, koridor)

    # ── 2. Edge transit ───────────────────────────────────────
    nama_map: dict[str, list] = {}
    for h in halte_list:
        nama_map.setdefault(_norm(h["nama"]), []).append(h)

    transit_count = 0
    for key, group in nama_map.items():
        pairs = [
            (group[i], group[j])
            for i in range(len(group))
            for j in range(i + 1, len(group))
            if group[i]["koridor"] != group[j]["koridor"]
        ]
        for a, b in pairs:
            ket = f"Transit {a['koridor']} <-> {b['koridor']}"
            _tambah_edge(edges, a["id"], b["id"],
                        waktu_transit, "TRANSIT", keterangan=ket)
            transit_count += 1

    print(f"  🔗 Total edge: {len(edges)} | Transit points: {transit_count}")

    # ── 3. Adjacency-list ─────────────────────────────────────
    graph: dict[str, list] = {h["id"]: [] for h in halte_list}
    for e in edges:
        graph[e["dari"]].append({
            "ke":          e["ke"],
            "waktu_menit": e["waktu_menit"],
            "koridor":     e["koridor"],
        })

    return graph


# ══════════════════════════════════════════════════════════════
# Hitung jarak total rute (KM)
# ══════════════════════════════════════════════════════════════

def hitung_jarak_rute(rute_id: list[str], halte_list: list) -> dict:
    id_ke_h = {h["id"]: h for h in halte_list}
    segmen  = []
    skip    = 0
    total   = 0.0
    prev    = None

    for hid in rute_id:
        h = id_ke_h.get(hid, {})
        if h.get("lat") and h.get("lon"):
            if prev:
                km = haversine(prev["lat"], prev["lon"], h["lat"], h["lon"])
                segmen.append({
                    "dari": prev["nama"],
                    "ke":   h["nama"],
                    "km":   round(km, 2),
                })
                total += km
            prev = h
        else:
            skip += 1

    return {
        "total_km":   round(total, 2),
        "segmen":     segmen,
        "halte_skip": skip,
    }

# ══════════════════════════════════════════════════════════════
# Load dari file
# ══════════════════════════════════════════════════════════════

def load_graph_dari_file(
    path_halte:    str       = "output/halte.json",
    bobot:         dict|None = None,
    waktu_transit: int       = WAKTU_TRANSIT_DEFAULT,
) -> tuple[dict, list]:

    if bobot is None:
        bobot = BOBOT_DEFAULT

    with open(path_halte, encoding="utf-8") as f:
        halte_list = json.load(f)

    graph = build_graph(halte_list, bobot, waktu_transit)
    return graph, halte_list
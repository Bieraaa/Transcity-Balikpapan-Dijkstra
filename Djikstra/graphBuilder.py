import json
import math
from itertools import groupby
from typing import Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════
# Bobot Waktu edge
# ══════════════════════════════════════════════════════════════

BOBOT_DEFAULT: Dict[str, float] = {
    "1" : 1.5,   # 95 menit ÷ 63 edge
    "2A": 2.2,   # 70 menit ÷ 32 edge
    "2B": 3.7,   # 70 menit ÷ 19 edge
}

WAKTU_TRANSIT_DEFAULT = 10  # menit estimasi pindah bus di halte transit

# ══════════════════════════════════════════════════════════════
# Tarif
# ══════════════════════════════════════════════════════════════

TARIF_PER_KORIDOR = 5_000
TARIF_PELAJAR     = 2_000


def hitung_biaya(koridor_dipakai: List[str], pelajar: bool = False) -> dict:
    # Strip sufiks "_balik" sebelum hitung biaya
    koridor_bersih = [
        k.replace("_balik", "")
        for k in koridor_dipakai
        if k not in ("TRANSIT",)
    ]
    # Deduplicate sambil jaga urutan (1 koridor = 1 tiket walau ada segmen balik)
    koridor_unik = list(dict.fromkeys(koridor_bersih))
    jumlah = len(koridor_unik)
    tarif  = TARIF_PELAJAR if pelajar else TARIF_PER_KORIDOR
    total  = jumlah * tarif
    detail = " + ".join(f"Kor.{k} (Rp {tarif:,})" for k in koridor_unik)

    return {
        "jumlah_tiket":    jumlah,
        "total_biaya":     total,
        "tarif_per_tiket": tarif,
        "detail":          detail,
        "tipe":            "Pelajar" if pelajar else "Umum",
    }


# ══════════════════════════════════════════════════════════════
# Haversine
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


def hitung_jarak_rute(rute_id: List[str], halte_list: list) -> dict:
    id_ke_h = {h["id"]: h for h in halte_list}
    segmen  = []
    total   = 0.0
    skip    = 0
    prev    = None

    for hid in rute_id:
        h = id_ke_h.get(hid, {})
        if h.get("lat") and h.get("lon"):
            if prev:
                km = haversine(prev["lat"], prev["lon"], h["lat"], h["lon"])
                segmen.append({"dari": prev["nama"], "ke": h["nama"], "km": round(km, 2)})
                total += km
            prev = h
        else:
            skip += 1

    return {"total_km": round(total, 2), "segmen": segmen, "halte_skip": skip}


# ══════════════════════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════════════════════

def _normalisasi(nama: str) -> str:
    return nama.lower().strip()


def _patch_koordinat(halte_list: list) -> list:
    for h in halte_list:
        if h.get("lat") is None or h.get("lon") is None:
            print(f"  ⚠️  Koordinat kosong: [{h['koridor']}] {h['nama']}")
    return halte_list


# ══════════════════════════════════════════════════════════════
# Build graph
# ══════════════════════════════════════════════════════════════

def build_graph(halte_list: list, bobot: dict, waktu_transit: int) -> dict:
    _patch_koordinat(halte_list)
    edges: List[dict] = []

    # Kelompokkan per koridor, urut ascending
    sorted_h = sorted(halte_list, key=lambda x: (x["koridor"], x["urutan"]))
    kor_map: Dict[str, list] = {}
    for kor, grp in groupby(sorted_h, key=lambda x: x["koridor"]):
        kor_map[kor] = sorted(list(grp), key=lambda x: x["urutan"])

    # 1. Edge MAJU dalam koridor (satu arah)
    for kor, halte_kor in kor_map.items():
        w = bobot.get(kor, 3)
        for j in range(len(halte_kor) - 1):
            a, b = halte_kor[j], halte_kor[j + 1]
            if a["lat"] is not None and b["lat"] is not None:
                edges.append({
                    "dari": a["id"], "ke": b["id"],
                    "waktu_menit": w, "koridor": kor
                })

    # 2. Edge TRANSIT dua arah (nama halte sama, koridor beda)
    nama_map: Dict[str, list] = {}
    for h in halte_list:
        nama_map.setdefault(_normalisasi(h["nama"]), []).append(h)

    transit_halte_ids: set = set()
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
                edges.append({"dari": a["id"], "ke": b["id"],
                              "waktu_menit": waktu_transit,
                              "koridor": "TRANSIT", "keterangan": ket})
                edges.append({"dari": b["id"], "ke": a["id"],
                              "waktu_menit": waktu_transit,
                              "koridor": "TRANSIT", "keterangan": ket})
                transit_halte_ids.add(a["id"])
                transit_halte_ids.add(b["id"])
                transit_count += 1

    # 3. Edge MUNDUR dari titik transit ke semua halte sebelumnya di koridor yang sama.
    #    Ini memungkinkan penumpang naik bus arah berlawanan setelah transit.
    #    Contoh: transit di Ace Hardware [2A, urutan 29], bisa mundur ke PLN MT Haryono [2A, urutan 15].
    #    Bobot = selisih_urutan × bobot_koridor (proporsional dengan jarak yang ditempuh).
    id_ke_halte = {h["id"]: h for h in halte_list}
    mundur_count = 0

    for hid in transit_halte_ids:
        h   = id_ke_halte.get(hid, {})
        kor = h.get("koridor", "")
        w   = bobot.get(kor, 3)

        for prev_h in kor_map.get(kor, []):
            if prev_h["urutan"] < h["urutan"] and prev_h["lat"] is not None:
                selisih = h["urutan"] - prev_h["urutan"]
                edges.append({
                    "dari":        hid,
                    "ke":          prev_h["id"],
                    "waktu_menit": selisih * w,
                    "koridor":     kor + "_balik",  # penanda arah mundur
                })
                mundur_count += 1

    print(f"  🔗 Edge maju: {len(edges) - transit_count*2 - mundur_count}"
          f"  |  Transit: {transit_count*2}"
          f"  |  Mundur: {mundur_count}"
          f"  |  Total: {len(edges)}")

    # 4. Bangun adjacency list
    graph: Dict[str, list] = {h["id"]: [] for h in halte_list}
    for e in edges:
        if e["dari"] in graph:
            graph[e["dari"]].append({
                "ke":          e["ke"],
                "waktu_menit": e["waktu_menit"],
                "koridor":     e["koridor"],
            })

    return graph  

# ══════════════════════════════════════════════════════════════
# Load dari file
# ══════════════════════════════════════════════════════════════

def load_graph_dari_file(
    path_halte: str = "output/halte.json",
    bobot: Optional[Dict] = None,
    waktu_transit: int = WAKTU_TRANSIT_DEFAULT,
) -> Tuple[dict, list]:

    if bobot is None:
        bobot = BOBOT_DEFAULT

    with open(path_halte, encoding="utf-8") as f:
        halte_list = json.load(f)

    graph = build_graph(halte_list, bobot, waktu_transit)
    return graph, halte_list
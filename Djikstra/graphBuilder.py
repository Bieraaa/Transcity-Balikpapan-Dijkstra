"""
Djikstra/graphBuilder.py
────────────────────────
Membangun adjacency-list graf dari halte.json untuk algoritma Dijkstra.

Perubahan dari versi sebelumnya:
  - Tidak lagi bergantung pada koordinat untuk membangun edge antar halte
    dalam satu koridor. Urutan halte ditentukan oleh field "urutan" di JSON.
    Dengan begitu, halte yang koordinatnya null pun tetap terhubung ke
    tetangganya — rute tidak putus hanya karena koordinat kosong.
  - Edge transit dibuat berdasarkan kesamaan nama halte lintas koridor.
  - Koordinat null hanya berdampak pada tampilan peta (titik tidak muncul),
    BUKAN pada perhitungan rute.
"""

import json
from itertools import groupby


# ══════════════════════════════════════════════════════════════
# Tarif
# ══════════════════════════════════════════════════════════════

TARIF_PER_KORIDOR = 5_000   # Rp 5.000 per koridor (umum)
TARIF_PELAJAR     = 2_000   # Rp 2.000 per koridor (pelajar)


def hitung_biaya(koridor_dipakai: list[str], pelajar: bool = False) -> dict:
    """
    Hitung biaya berdasarkan jumlah koridor unik yang dinaiki.

    Returns dict:
        jumlah_tiket  : int
        total_biaya   : int
        detail        : str  (misal "Kor.1 (Rp 5.000) + Kor.2A (Rp 5.000)")
        tipe          : str  ("Umum" | "Pelajar")
    """
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
# Helper internal
# ══════════════════════════════════════════════════════════════

def _norm(nama: str) -> str:
    """Normalisasi nama untuk pencocokan transit (lower + strip)."""
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

def build_graph(halte_list: list, bobot: dict, waktu_transit: int) -> dict:
    """
    Bangun adjacency-list dari data halte.

    Aturan:
    1. Edge dalam koridor: sambungkan halte[urutan N] → halte[urutan N+1]
       TANPA syarat koordinat harus ada. Semua halte dalam satu koridor
       pasti terhubung berurutan selama field "urutan" konsisten.
    2. Edge transit: halte dengan nama SAMA di koridor BERBEDA dihubungkan
       dengan waktu waktu_transit menit.

    Args:
        halte_list    : list dict dari halte.json
        bobot         : {koridor_str: waktu_menit_per_edge}
        waktu_transit : waktu pindah bus di halte transit (menit)

    Returns:
        adjacency-list  {id_halte: [{"ke":..., "waktu_menit":..., "koridor":...}]}
    """
    edges: list[dict] = []

    # ── 1. Edge dalam koridor ──────────────────────────────────
    sorted_h = sorted(halte_list, key=lambda x: (x["koridor"], x["urutan"]))
    for koridor, grp in groupby(sorted_h, key=lambda x: x["koridor"]):
        halte_kor = list(grp)
        w = bobot.get(koridor, 3)
        for j in range(len(halte_kor) - 1):
            a, b = halte_kor[j], halte_kor[j + 1]
            # Edge dibuat tanpa syarat koordinat
            _tambah_edge(edges, a["id"], b["id"], w, koridor)

    # ── 2. Edge transit ───────────────────────────────────────
    nama_map: dict[str, list] = {}
    for h in halte_list:
        key = _norm(h["nama"])
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
            ket = f"Transit {a['koridor']} <-> {b['koridor']}"
            _tambah_edge(edges, a["id"], b["id"], waktu_transit, "TRANSIT",
                         keterangan=ket)
            transit_count += 1

    total_edge = len(edges)
    print(f"  🔗 Total edge: {total_edge} | Transit points: {transit_count}")

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
# Load dari file
# ══════════════════════════════════════════════════════════════

def load_graph_dari_file(
    path_halte:    str       = "output/halte.json",
    bobot:         dict|None = None,
    waktu_transit: int       = 10,
) -> tuple[dict, list]:
    """
    Load halte.json dan bangun graf.

    Returns:
        (graph, halte_list)
    """
    if bobot is None:
        bobot = {"1": 4, "2A": 2, "2B": 4}

    with open(path_halte, encoding="utf-8") as f:
        halte_list = json.load(f)

    graph = build_graph(halte_list, bobot, waktu_transit)
    return graph, halte_list
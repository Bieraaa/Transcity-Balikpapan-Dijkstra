import json
from itertools import groupby
from pathlib import Path

# ==== Helper ====

def normalisasi_nama(nama: str) -> str:
    """Normalisasi nama halte untuk deteksi transit antar koridor.
    Hanya lowercase + strip spasi — TIDAK buang huruf akhir karena
    bisa memotong nama asli (mis. 'Ibnu Sina' -> 'Ibnu Sin').
    """
    return nama.lower().strip()

def _tambah_edge(edges: list, dari: str, ke: str, waktu: int, koridor: str, **extra):
    """Tambah satu edge + edge baliknya (2 arah)."""
    base  = {"dari": dari, "ke": ke,   "waktu_menit": waktu, "koridor": koridor, **extra}
    balik = {"dari": ke,   "ke": dari, "waktu_menit": waktu, "koridor": koridor, **extra}
    edges.extend([base, balik])

# ==== Graph Halte Bis ====

def build_graph(halte_list: list, bobot: dict, waktu_transit: int) -> dict:
    """
    Bangun adjacency list dari data halte.

    Args:
        halte_list   : list halte (dari halte.json)
        bobot        : dict bobot waktu per koridor, e.g. {"1": 4, "2A": 2, "2B": 4}
        waktu_transit: waktu pindah koridor (menit)

    Returns:
        dict {id_halte: [{"ke", "waktu_menit", "koridor"}, ...]}
    """
    edges = []

    # 1. Koneksi berurutan dalam koridor yang sama
    sorted_h = sorted(halte_list, key=lambda x: (x["koridor"], x["urutan"]))
    for koridor, grp in groupby(sorted_h, key=lambda x: x["koridor"]):
        halte_kor = list(grp)
        w = bobot.get(koridor, 3)
        for j in range(len(halte_kor) - 1):
            a, b = halte_kor[j], halte_kor[j + 1]
            # Fix: cek is not None, bukan truthy (lat=0.0 valid tapi falsy)
            if a["lat"] is not None and b["lat"] is not None:
                _tambah_edge(edges, a["id"], b["id"], w, koridor)

    # 2. Koneksi transit antar koridor (nama halte sama persis)
    nama_map: dict[str, list] = {}
    for h in halte_list:
        key = normalisasi_nama(h["nama"])
        nama_map.setdefault(key, []).append(h)

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
                _tambah_edge(edges, a["id"], b["id"], waktu_transit, "TRANSIT", keterangan=ket)

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
    """
    Shortcut: load halte.json lalu langsung build graph.

    Returns:
        (graph, halte_list)
    """
    if bobot is None:
        # Fix: pakai nama koridor yang benar (1, 2A, 2B)
        bobot = {"1": 4, "2A": 2, "2B": 4}

    with open(path_halte, encoding="utf-8") as f:
        halte_list = json.load(f)

    graph = build_graph(halte_list, bobot, waktu_transit)
    return graph, halte_list
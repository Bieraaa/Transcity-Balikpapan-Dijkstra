import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════
# Data struktur hasil
# ══════════════════════════════════════════════════════════════

@dataclass
class TransitInfo:
    di_halte_id:   str
    di_halte_nama: str
    dari_koridor:  str
    ke_koridor:    str


@dataclass
class RuteResult:
    ditemukan:       bool
    id_asal:         str
    id_tujuan:       str
    nama_asal:       str
    nama_tujuan:     str
    rute_id:         List[str]
    rute_nama:       List[str]
    rute_koridor:    List[str]   
    total_waktu:     int         
    jumlah_halte:    int         
    transit:         List[TransitInfo]   
    koridor_dipakai: List[str]
    total_biaya:     int   = 0
    detail_biaya:    str   = ""
    tipe_penumpang:  str   = "Umum"
    pesan:           str   = ""
    total_km:        float = 0.0
    segmen_km:       List  = field(default_factory=list)


# ══════════════════════════════════════════════════════════════
# Algoritma Dijkstra
# ══════════════════════════════════════════════════════════════

def _dijkstra_raw(graph: dict, id_asal: str) -> Tuple[dict, dict]:
    dist = {node: float("inf") for node in graph}
    prev = {node: None for node in graph}
    dist[id_asal] = 0.0
    pq = [(0.0, id_asal)]

    while pq:
        jarak_skrg, node = heapq.heappop(pq)
        if jarak_skrg > dist[node]:
            continue
        for tetangga in graph.get(node, []):
            ke         = tetangga["ke"]
            waktu      = tetangga["waktu_menit"]
            jarak_baru = dist[node] + waktu
            if jarak_baru < dist[ke]:
                dist[ke] = jarak_baru
                prev[ke] = (node, tetangga["koridor"])
                heapq.heappush(pq, (jarak_baru, ke))

    return dist, prev

def _rekonstruksi(prev: dict, id_tujuan: str) -> List[Tuple]:
    path = []
    node = id_tujuan
    while node is not None:
        info = prev.get(node)
        if info:
            path.append((node, info[1]))
            node = info[0]
        else:
            path.append((node, None))
            break
    path.reverse()
    return path


def _deteksi_transit(path: List[Tuple], id_ke_halte: dict) -> List[TransitInfo]:
    """
    Deteksi perpindahan koridor aktual.
    Transit terjadi saat edge berubah dari koridor X ke koridor Y.
    """
    transit       = []
    koridor_aktif = None

    for i, (hid, edge_kor) in enumerate(path):
        if edge_kor is None or edge_kor == "TRANSIT":
            continue
        if koridor_aktif is None:
            koridor_aktif = edge_kor
            continue
        if edge_kor != koridor_aktif:
            halte_transit_id = path[i - 1][0]
            h = id_ke_halte.get(halte_transit_id, {})
            transit.append(TransitInfo(
                di_halte_id   = halte_transit_id,
                di_halte_nama = h.get("nama", halte_transit_id),
                dari_koridor  = koridor_aktif,
                ke_koridor    = edge_kor,
            ))
            koridor_aktif = edge_kor
    return transit


def _bangun_rute_koridor(path: List[Tuple]) -> List[str]:
    rute_koridor  = []
    koridor_aktif = None
    for _, edge_kor in path:
        if edge_kor and edge_kor != "TRANSIT":
            koridor_aktif = edge_kor
        rute_koridor.append(koridor_aktif or "1")
    return rute_koridor


def _deteksi_rute_memutar(
        rute_id: List[str],
        halte_list: list,
        koridor_dipakai: List[str],
) -> Optional[str]:

    if len(koridor_dipakai) != 1:
        return None

    kor    = koridor_dipakai[0]
    total  = sum(1 for h in halte_list if h["koridor"] == kor)
    dipakai = len(rute_id)

    if total > 0 and dipakai / total > 0.75:
        return (
            f"⚠️  Rute ini melewati {dipakai} dari {total} halte Koridor {kor} "
            f"({dipakai / total * 100:.0f}%). "
            f"Kemungkinan bus perlu menempuh hampir seluruh jalur koridor. "
            f"Pastikan asal dan tujuan berada di arah yang sama."
        )
    return None

# ══════════════════════════════════════════════════════════════
# Fungsi utama
# ══════════════════════════════════════════════════════════════

def cari_rute(
    graph:      dict,
    halte_list: list,
    id_asal:    str,
    id_tujuan:  str,
    pelajar:    bool = False,
) -> RuteResult:

    from graphBuilder import hitung_biaya, hitung_jarak_rute

    id_ke_halte = {h["id"]: h for h in halte_list}

    def nama(hid):
        return id_ke_halte.get(hid, {}).get("nama", hid)

    # Validasi
    if id_asal not in graph:
        return RuteResult(False, id_asal, id_tujuan,
                        nama(id_asal), nama(id_tujuan),
                        [], [], [], 0, 0, [], [],
                        pesan=f"ID '{id_asal}' tidak ditemukan.")
    if id_tujuan not in graph:
        return RuteResult(False, id_asal, id_tujuan,
                        nama(id_asal), nama(id_tujuan),
                        [], [], [], 0, 0, [], [],
                        pesan=f"ID '{id_tujuan}' tidak ditemukan.")
    if id_asal == id_tujuan:
        n = nama(id_asal)
        return RuteResult(True, id_asal, id_tujuan, n, n,
                        [id_asal], [n], ["1"], 0, 1, [], [],
                        pesan="Asal dan tujuan sama.")

    # Dijkstra
    dist, prev = _dijkstra_raw(graph, id_asal)

    if dist[id_tujuan] == float("inf"):
        return RuteResult(
            False, id_asal, id_tujuan, nama(id_asal), nama(id_tujuan),
            [], [], [], 0, 0, [], [],
            pesan=(
                "Tidak ada jalur yang menghubungkan kedua halte.\n"
                "Kemungkinan tujuan berada sebelum asal dalam arah rute, "
                "atau belum ada koneksi transit."
            )
        )

    path         = _rekonstruksi(prev, id_tujuan)
    rute_id      = [p[0] for p in path]
    rute_nama    = [id_ke_halte.get(p[0], {}).get("nama", p[0]) for p in path]
    rute_koridor = _bangun_rute_koridor(path)
    transit_info = _deteksi_transit(path, id_ke_halte)

    koridor_dipakai = list(dict.fromkeys(
        p[1] for p in path if p[1] and p[1] != "TRANSIT"
    ))

    biaya      = hitung_biaya(koridor_dipakai, pelajar=pelajar)
    jarak_info = hitung_jarak_rute(rute_id, halte_list)
    pesan      = _deteksi_rute_memutar(rute_id, halte_list, koridor_dipakai)

    return RuteResult(
        ditemukan       = True,
        id_asal         = id_asal,
        id_tujuan       = id_tujuan,
        nama_asal       = nama(id_asal),
        nama_tujuan     = nama(id_tujuan),
        rute_id         = rute_id,
        rute_nama       = rute_nama,
        rute_koridor    = rute_koridor,
        total_waktu     = round(dist[id_tujuan], 1),
        jumlah_halte    = len(rute_id),
        transit         = transit_info,
        koridor_dipakai = koridor_dipakai,
        total_biaya     = biaya["total_biaya"],
        detail_biaya    = biaya["detail"],
        tipe_penumpang  = biaya["tipe"],
        pesan           = pesan or "",
        total_km        = jarak_info["total_km"],
        segmen_km       = jarak_info["segmen"],
    )
import heapq
from dataclasses import dataclass, field

# ===== Data hasil pencarian =====

@dataclass
class TransitInfo:
    di_halte_id:    str
    di_halte_nama:  str
    dari_koridor:   str
    ke_koridor:     str

@dataclass
class RuteResult:
    ditemukan:      bool
    id_asal:        str
    id_tujuan:      str
    nama_asal:      str
    nama_tujuan:    str
    rute_id:        list[str]
    rute_nama:      list[str]
    total_waktu:    int
    jumlah_halte:   int
    transit:         list[TransitInfo]
    koridor_dipakai:list[str]
    pesan:          str = " "

# ==== Algoritma Djikstra ====

def djikstra_raw(graph: dict, id_asal: str) -> tuple[dict, dict]:
    dist = {
        node: float("inf") for node in graph
    }
    prev = {
        node: None for node in graph
    }
    dist[id_asal] = 0

    # priority queue: (jarak, id_halte)
    pq = [(0, id_asal)]

    while pq:
        jarak_sekarang, node = heapq.heappop(pq)

        # Skip kalau ketemu jarak lebih pendek
        if jarak_sekarang > dist[node]:
            continue

        for tetangga in graph.get(node, []):
            ke = tetangga["ke"]
            waktu = tetangga["waktu_menit"]
            koridor = tetangga["koridor"]

            jarak_baru = dist[node] + waktu
            if jarak_baru < dist[ke]:
                dist[ke] = jarak_baru
                prev[ke] = (node, koridor)
                heapq.heappush(pq, (jarak_baru, ke))

    return dist, prev

def _rekontruksi_path(prev: dict, id_asal: str, id_tujuan: str) -> list[tuple]:
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

def _deteksi_transit(path: list[tuple]) -> list[TransitInfo]:
    transit = []
    for i in range(1, len(path)):
        kor_prev = path[i - 1][1]
        kor_curr = path[i][1]
        if(
            kor_prev is not None
            and kor_curr is not None
            and kor_prev != kor_curr
            and "TRANSIT" in (kor_prev, kor_curr)
        ):
            transit.append(path[i][0]) #id halte transit
    return transit

# ==== Fungsi di GUI ====

def cari_rute(
        graph:      dict,
        halte_list: list,
        id_asal:    str,
        id_tujuan:  str,
) -> RuteResult:
    
    # buat lookup id -> nama halte
    id_ke_halte = {
        h["id"]: h for h in halte_list
    }

    # validasi input
    if id_asal not in graph:
        return RuteResult(
            False, id_asal, id_tujuan, "?", "?", [], [], 0, 0, [], [], pesan=f"ID asal '{id_asal}' tidak ditemukan." 
        )
    
    if id_tujuan not in graph:
        return RuteResult(
            False, id_asal, id_tujuan, "?", "?", [], [], 0, 0, [], [], pesan=f"ID tujuan '{id_tujuan}' tidak ditemukan."
        )
    
    if id_asal == id_tujuan:
        nama = id_ke_halte[id_asal]["nama"]
        return RuteResult(
            True, id_asal, id_tujuan, nama, nama, [id_asal], [nama], 0, 1, [], [], pesan="Asal dan tujuan sama."
        )
    
    # Jalankan di Djikstra
    dist, prev = djikstra_raw(graph, id_asal)

    # Tidak ada jalur
    if dist[id_tujuan] == float("inf"):
        return RuteResult(
            False, id_asal, id_tujuan,
            id_ke_halte.get(id_asal, {}).get("nama", "?"),
            id_ke_halte.get(id_tujuan, {}).get("nama", "?"),
            [], [], 0, 0, [], [],
            pesan="Tidak ada jalur yang menghubungkan kedua halte."
        )
    
    # Rekontruksi Path
    path = _rekontruksi_path(prev, id_asal, id_tujuan)
    rute_id = [p[0] for p in path]
    rute_nama = [id_ke_halte.get(p[0], {}).get("nama", p[0]) for p in path]

    # Deteksi Transit
    transit_id = _deteksi_transit(path)
    transit_info = []
    for i, tid in enumerate(transit_id):
        h = id_ke_halte.get(tid, {}) # Cari peubahan koridor di sekitar titik transit
        idx = rute_id.index(tid)
        kor_dari = path[idx - 1][1] if idx > 0 else "?"
        kor_ke = path[idx][1] if idx < len(path) else "?"
        transit_info.append(TransitInfo(
            di_halte_id     = tid,
            di_halte_nama   = h.get("nama", tid),
            dari_koridor    = kor_dari.replace("TRANSIT", "").strip() or kor_dari,
            ke_koridor      = kor_ke.replace("TRANSIT", "").strip() or kor_ke
        ))

    # Korudor unik yang dipakai (Tanpa Transit)
    koridor_dipakai = list(dict.fromkeys(
        p[1] for p in path if p[1] and p[1] != "TRANSIT"
    ))

    return RuteResult(
        ditemukan       =   True,
        id_asal         =   id_asal,
        id_tujuan       =   id_tujuan,
        nama_asal       =   id_ke_halte.get(id_asal,{}).get("nama", id_asal),
        nama_tujuan     =   id_ke_halte.get(id_tujuan, {}).get("nama", id_tujuan),
        rute_id         =   rute_id,
        rute_nama       =   rute_nama,
        total_waktu     =   dist[id_tujuan],
        jumlah_halte    =   len(rute_id),
        transit          =   transit_info,
        koridor_dipakai =   koridor_dipakai
    )
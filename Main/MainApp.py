import os
import sys
import json
import tempfile
import requests
import folium

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFrame, QScrollArea,
    QSizePolicy, QCheckBox, QSplitter
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Djikstra.graphBuilder import load_graph_dari_file
from Djikstra.Djikstra import cari_rute, RuteResult

# ── Konstanta ──────────────────────────────────────────────────────
HALTE_JSON   = os.path.join(os.path.dirname(__file__), "..", "output", "halte.json")
OSRM_URL     = "http://router.project-osrm.org/route/v1/driving"
BALIKPAPAN_CENTER = [-1.270, 116.860]

WARNA_KORIDOR = {
    "1":      "#E74C3C",   # merah
    "2A":     "#3498DB",   # biru
    "2B":     "#2ECC71",   # hijau
    "TRANSIT": "#F39C12",  # oranye
}

# =========================================
# OSRM Helper 
# =========================================

def get_osrm_route(coords: list[tuple]) -> list[list] | None:
    """
    Minta geometri rute ke OSRM (mengikuti jalan asli).
    coords: list of (lat, lon)
    Return: list of [lat, lon] untuk folium PolyLine, atau None kalau gagal.
    """
    if len(coords) < 2:
        return None

    # OSRM pakai format lon,lat (terbalik dari folium!)
    waypoints = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"{OSRM_URL}/{waypoints}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok":
            # GeoJSON coordinates: [lon, lat] → balik ke [lat, lon] untuk folium
            geojson_coords = data["routes"][0]["geometry"]["coordinates"]
            return [[lat, lon] for lon, lat in geojson_coords]
    except Exception as e:
        print(f"  ⚠️ OSRM error: {e} — pakai garis lurus sebagai fallback")
    return None

def build_folium_map(result: RuteResult, halte_list: list) -> str:
    """
    Buat peta folium dengan rute yang mengikuti jalan (via OSRM).
    Return path ke file HTML sementara.
    """
    id_ke_halte = {h["id"]: h for h in halte_list}

    m = folium.Map(
        location=BALIKPAPAN_CENTER,
        zoom_start=13,
        tiles="OpenStreetMap",
    )

    if not result.ditemukan or not result.rute_id:
        # Kalau tidak ada rute, tampilkan peta kosong
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w")
        m.save(tmp.name)
        return tmp.name

    # Kumpulkan koordinat tiap halte di rute
    coords_rute = []
    for hid in result.rute_id:
        h = id_ke_halte.get(hid, {})
        if h.get("lat") and h.get("lon"):
            coords_rute.append((h["lat"], h["lon"]))

    # ── Gambar rute per segmen koridor (warna berbeda) ──
    # Deteksi segmen: kelompokkan halte berurutan per koridor
    segmen: list[dict] = []
    seg_coords = [coords_rute[0]] if coords_rute else []
    seg_kor = None

    # Rebuild path dengan info koridor
    from Djikstra.graphBuilder import load_graph_dari_file
    # Pakai warna per segmen berdasarkan koridor
    path_info = []
    for i, hid in enumerate(result.rute_id):
        h = id_ke_halte.get(hid, {})
        kor = h.get("koridor", "1")
        path_info.append((hid, kor))

    # Gambar polyline per segmen koridor
    i = 0
    while i < len(path_info) - 1:
        kor_skrg = path_info[i][1]
        seg = [i]
        j = i + 1
        while j < len(path_info) and path_info[j][1] == kor_skrg:
            seg.append(j)
            j += 1
        seg.append(j if j < len(path_info) else j - 1)

        seg_coords_latlon = []
        for idx in seg:
            if idx < len(result.rute_id):
                h = id_ke_halte.get(result.rute_id[idx], {})
                if h.get("lat") and h.get("lon"):
                    seg_coords_latlon.append((h["lat"], h["lon"]))

        if len(seg_coords_latlon) >= 2:
            # Coba OSRM dulu
            osrm_coords = get_osrm_route(seg_coords_latlon)
            line_coords = osrm_coords if osrm_coords else seg_coords_latlon
            warna = WARNA_KORIDOR.get(kor_skrg, "#7F8C8D")

            folium.PolyLine(
                locations=line_coords,
                color=warna,
                weight=5,
                opacity=0.85,
                tooltip=f"Koridor {kor_skrg}",
            ).add_to(m)

        i = j if j < len(path_info) else j

    # ── Marker tiap halte ──
    transit_ids = {t.di_halte_id for t in result.transit}

    for i, hid in enumerate(result.rute_id):
        h = id_ke_halte.get(hid, {})
        if not h.get("lat"):
            continue

        nama = h.get("nama", hid)
        lat, lon = h["lat"], h["lon"]

        if hid == result.rute_id[0]:
            # Asal → hijau
            icon = folium.Icon(color="green", icon="play", prefix="fa")
            popup_text = f"🟢 ASAL: {nama}"
        elif hid == result.rute_id[-1]:
            # Tujuan → merah
            icon = folium.Icon(color="red", icon="flag", prefix="fa")
            popup_text = f"🔴 TUJUAN: {nama}"
        elif hid in transit_ids:
            # Transit → oranye
            icon = folium.Icon(color="orange", icon="exchange", prefix="fa")
            t = next((t for t in result.transit if t.di_halte_id == hid), None)
            kor_info = f"Kor.{t.dari_koridor} → Kor.{t.ke_koridor}" if t else ""
            popup_text = f"🔄 TRANSIT: {nama}<br>{kor_info}"
        else:
            # Halte biasa → abu
            icon = folium.Icon(color="gray", icon="bus", prefix="fa")
            popup_text = f"🚏 {i+1}. {nama}"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=200),
            tooltip=nama,
            icon=icon,
        ).add_to(m)

    # Fit bounds ke semua titik rute
    if coords_rute:
        m.fit_bounds([[min(c[0] for c in coords_rute) - 0.01,
                        min(c[1] for c in coords_rute) - 0.01],
                        [max(c[0] for c in coords_rute) + 0.01,
                        max(c[1] for c in coords_rute) + 0.01]])

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    m.save(tmp.name)
    return tmp.name

# =========================================
# Worker Thread (Dijkstra + OSRM tidak blocking UI)
# =========================================

class RouteWorker(QThread):
    selesai = pyqtSignal(object, str)   # (RuteResult, path_html)

    def __init__(self, graph, halte_list, id_asal, id_tujuan, pelajar):
        super().__init__()
        self.graph      = graph
        self.halte_list = halte_list
        self.id_asal    = id_asal
        self.id_tujuan  = id_tujuan
        self.pelajar    = pelajar

    def run(self):
        result   = cari_rute(self.graph, self.halte_list,self.id_asal, self.id_tujuan, self.pelajar)
        html_path = build_folium_map(result, self.halte_list)
        self.selesai.emit(result, html_path)

# =========================================
# Main Window 
# =========================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Balikpapan City Trans — Route Finder")
        self.setMinimumSize(1100, 700)

        self.graph      = None
        self.halte_list = []
        self.worker     = None
        self._tmp_html  = None

        self._setup_ui()
        self._load_data()
# =========================================
# Setup UI
# =========================================

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Splitter: panel kiri | peta kanan
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ── Panel kiri ──
        left = QWidget()
        left.setFixedWidth(340)
        left.setStyleSheet("background:#1a1a2e;")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(16, 16, 16, 16)
        lv.setSpacing(12)

        # Header
        title = QLabel("🚌 Bacitra Route Finder")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color:#e2e2e2;")
        lv.addWidget(title)

        subtitle = QLabel("Balikpapan City Trans")
        subtitle.setStyleSheet("color:#7f8c9a; font-size:11px;")
        lv.addWidget(subtitle)

        lv.addWidget(self._divider())

        # Dropdown asal
        lv.addWidget(self._label("📍 Halte Asal"))
        self.combo_asal = self._combo()
        lv.addWidget(self.combo_asal)

        # Dropdown tujuan
        lv.addWidget(self._label("🏁 Halte Tujuan"))
        self.combo_tujuan = self._combo()
        lv.addWidget(self.combo_tujuan)

        # Checkbox pelajar
        self.chk_pelajar = QCheckBox("Tarif Pelajar (Rp 2.000/koridor)")
        self.chk_pelajar.setStyleSheet("color:#bdc3c7; font-size:12px;")
        lv.addWidget(self.chk_pelajar)

        # Tombol cari
        self.btn_cari = QPushButton("🔍  Cari Rute")
        self.btn_cari.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_cari.setFixedHeight(44)
        self.btn_cari.setStyleSheet("""
            QPushButton {
                background: #2980b9;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #3498db; }
            QPushButton:disabled { background: #555; color: #888; }
        """)
        self.btn_cari.clicked.connect(self._cari_rute)
        lv.addWidget(self.btn_cari)

        lv.addWidget(self._divider())

        # Panel hasil (scrollable)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:#1a1a2e; border:none;")
        self.hasil_widget = QWidget()
        self.hasil_layout = QVBoxLayout(self.hasil_widget)
        self.hasil_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.hasil_widget)
        lv.addWidget(self.scroll)

        # Status
        self.lbl_status = QLabel("Memuat data...")
        self.lbl_status.setStyleSheet("color:#7f8c9a; font-size:10px;")
        lv.addWidget(self.lbl_status)

        splitter.addWidget(left)

        # ── Peta kanan ──
        self.map_view = QWebEngineView()
        self.map_view.setStyleSheet("background:#0f0f1e;")
        splitter.addWidget(self.map_view)
        splitter.setSizes([340, 760])

        # Tampilkan peta awal kosong
        self._tampilkan_peta_kosong()

    def _label(self, text):
        l = QLabel(text)
        l.setStyleSheet("color:#bdc3c7; font-size:12px; font-weight:600;")
        return l

    def _combo(self):
        c = QComboBox()
        c.setEditable(True)
        c.setFixedHeight(36)
        c.setStyleSheet("""
            QComboBox {
                background: #16213e;
                color: #e2e2e2;
                border: 1px solid #2c3e50;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background: #16213e;
                color: #e2e2e2;
                selection-background-color: #2980b9;
            }
        """)
        return c

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background:#2c3e50; max-height:1px;")
        return line
# =========================================
# Load data 
# =========================================

    def _load_data(self):
        if not os.path.exists(HALTE_JSON):
            self.lbl_status.setText("❌ halte.json tidak ditemukan! Jalankan run_geocoder.py dulu.")
            return
        try:
            self.graph, self.halte_list = load_graph_dari_file(HALTE_JSON)
            self._isi_combo()
            total_edge = sum(len(v) for v in self.graph.values())
            self.lbl_status.setText(
                f"✅ {len(self.halte_list)} halte | {total_edge} edge"
            )
        except Exception as e:
            self.lbl_status.setText(f"❌ Error: {e}")

    def _isi_combo(self):
        # Urutkan: nama halte, tampilkan koridor di belakang
        items = sorted(
            [(f"{h['nama']}  [{h['koridor']}]", h["id"]) for h in self.halte_list],
            key=lambda x: x[0]
        )
        for combo in (self.combo_asal, self.combo_tujuan):
            combo.clear()
            for label, hid in items:
                combo.addItem(label, userData=hid)
# =========================================
# Cari rute 
# =========================================

    def _cari_rute(self):
        if self.graph is None:
            return

        id_asal   = self.combo_asal.currentData()
        id_tujuan = self.combo_tujuan.currentData()
        pelajar   = self.chk_pelajar.isChecked()

        if not id_asal or not id_tujuan:
            self.lbl_status.setText("⚠️ Pilih halte asal dan tujuan.")
            return

        self.btn_cari.setEnabled(False)
        self.btn_cari.setText("⏳  Mencari rute...")
        self.lbl_status.setText("Menghitung rute + mengambil data jalan...")

        self.worker = RouteWorker(
            self.graph, self.halte_list, id_asal, id_tujuan, pelajar
        )
        self.worker.selesai.connect(self._tampilkan_hasil)
        self.worker.start()

    def _tampilkan_hasil(self, result: RuteResult, html_path: str):
        self.btn_cari.setEnabled(True)
        self.btn_cari.setText("🔍  Cari Rute")

        # Bersihkan hasil sebelumnya
        for i in reversed(range(self.hasil_layout.count())):
            w = self.hasil_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not result.ditemukan:
            self._tambah_card("❌ Rute tidak ditemukan", result.pesan, "#c0392b")
            self.lbl_status.setText("Rute tidak ditemukan.")
            self._tampilkan_peta_kosong()
            return

        # Card ringkasan
        ringkasan = (
            f"⏱ Waktu tempuh  : {result.total_waktu} menit\n"
            f"🚏 Jumlah halte  : {result.jumlah_halte} halte\n"
            f"🛤 Koridor        : {' → '.join(result.koridor_dipakai)}\n"
            f"💰 Biaya ({result.tipe_penumpang}) : Rp {result.total_biaya:,}"
        )
        self._tambah_card("✅ Rute Ditemukan", ringkasan, "#27ae60")

        # Card transit (jika ada)
        if result.transit:
            transit_text = ""
            for t in result.transit:
                transit_text += f"🔄 Di {t.di_halte_nama}\n"
                transit_text += f"   Kor.{t.dari_koridor} → Kor.{t.ke_koridor}\n"
            self._tambah_card(f"Transit ({len(result.transit)}x)", transit_text.strip(), "#e67e22")

        # Card urutan halte
        urutan_text = ""
        transit_ids = {t.di_halte_id for t in result.transit}
        for i, (hid, nama) in enumerate(zip(result.rute_id, result.rute_nama)):
            if hid == result.rute_id[0]:
                prefix = "🟢"
            elif hid == result.rute_id[-1]:
                prefix = "🔴"
            elif hid in transit_ids:
                prefix = "🔄"
            else:
                prefix = "●"
            urutan_text += f"{prefix} {i+1:02d}. {nama}\n"
        self._tambah_card("📍 Urutan Halte", urutan_text.strip(), "#2c3e50")

        # Tampilkan peta
        if self._tmp_html:
            try:
                os.unlink(self._tmp_html)
            except Exception:
                pass
        self._tmp_html = html_path
        self.map_view.load(QUrl.fromLocalFile(html_path))

        self.lbl_status.setText(
            f"Rute: {result.nama_asal} → {result.nama_tujuan} | "
            f"{result.total_waktu} mnt | Rp {result.total_biaya:,}"
        )

    def _tambah_card(self, judul: str, isi: str, warna: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #16213e;
                border-left: 4px solid {warna};
                border-radius: 6px;
                padding: 8px;
                margin-bottom: 4px;
            }}
        """)
        cv = QVBoxLayout(card)
        cv.setContentsMargins(8, 6, 8, 6)
        cv.setSpacing(4)

        lbl_judul = QLabel(judul)
        lbl_judul.setStyleSheet(f"color:{warna}; font-weight:bold; font-size:12px;")
        cv.addWidget(lbl_judul)

        lbl_isi = QLabel(isi)
        lbl_isi.setStyleSheet("color:#bdc3c7; font-size:11px;")
        lbl_isi.setWordWrap(True)
        cv.addWidget(lbl_isi)

        self.hasil_layout.addWidget(card)

    def _tampilkan_peta_kosong(self):
        m = folium.Map(location=BALIKPAPAN_CENTER, zoom_start=13)
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,mode="w", encoding="utf-8")
        m.save(tmp.name)
        self.map_view.load(QUrl.fromLocalFile(tmp.name))

# =========================================
#  Entry point
# =========================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
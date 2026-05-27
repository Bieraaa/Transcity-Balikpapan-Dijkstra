"""
gui/app.py
──────────
GUI PyQt5 untuk pencarian rute Balikpapan City Trans.

Perubahan UI:
  ✅ Font lebih besar di panel kiri (mudah dibaca)
  ✅ Node asal  → hijau
  ✅ Node tujuan → merah
  ✅ Node transit → biru
  ✅ Node dilewati → abu gelap (filled)
  ✅ Node tidak dilewati → abu terang kecil
  ✅ Jalur utama → hijau terang (#00E676)
  ✅ Jalur alternatif (jika ada) → biru / kuning
"""

import os
import sys
import json
import tempfile
import requests
import folium
from folium.plugins import AntPath

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFrame, QScrollArea,
    QCheckBox, QSplitter
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Djikstra.graphBuilder import load_graph_dari_file
from Djikstra.Djikstra import cari_rute, RuteResult

# ── Konstanta ──────────────────────────────────────────────────────
HALTE_JSON        = os.path.join(os.path.dirname(__file__), "..", "output", "halte.json")
OSRM_URL          = "http://router.project-osrm.org/route/v1/driving"
BALIKPAPAN_CENTER = [-1.270, 116.860]

# Warna jalur utama dan alternatif
WARNA_JALUR_UTAMA = "#00E676"   # hijau terang
WARNA_JALUR_ALT   = ["#2196F3", "#FFC107"]  # biru, kuning (untuk rute alternatif)

# Warna marker node (sesuai permintaan)
WARNA_NODE = {
    "asal":     "green",   # hijau
    "tujuan":   "red",     # merah
    "transit":  "blue",    # biru
    "dilewati": "darkgray",# abu gelap
    "biasa":    "lightgray",# abu terang (halte tidak dilewati)
}


# ── OSRM Helper ────────────────────────────────────────────────────

def get_osrm_route(coords: list[tuple]) -> list[list] | None:
    """
    Minta geometri rute ke OSRM (mengikuti jalan asli).
    coords: list of (lat, lon)
    Return: list of [lat, lon] untuk folium PolyLine, atau None kalau gagal.
    """
    if len(coords) < 2:
        return None
    waypoints = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url    = f"{OSRM_URL}/{waypoints}"
    params = {"overview": "full", "geometries": "geojson"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok":
            geojson_coords = data["routes"][0]["geometry"]["coordinates"]
            return [[lat, lon] for lon, lat in geojson_coords]
    except Exception as e:
        print(f"  ⚠️ OSRM error: {e} — pakai garis lurus sebagai fallback")
    return None


def _circle_marker(m, lat, lon, color, radius, tooltip, popup_text, fill_color=None):
    """Helper: tambah CircleMarker ke peta."""
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=fill_color or color,
        fill_opacity=0.9,
        weight=2,
        tooltip=tooltip,
        popup=folium.Popup(popup_text, max_width=220),
    ).add_to(m)


def build_folium_map(result: RuteResult, halte_list: list) -> str:
    """
    Buat peta folium:
      - Jalur utama: hijau terang, mengikuti jalan (OSRM)
      - Node asal: hijau | tujuan: merah | transit: biru
      - Node dilewati: abu gelap | tidak dilewati: abu terang kecil
    """
    id_ke_halte = {h["id"]: h for h in halte_list}

    m = folium.Map(
        location=BALIKPAPAN_CENTER,
        zoom_start=13,
        tiles="OpenStreetMap",
    )

    # ── Semua halte (abu terang, kecil) ── tampil selalu sebagai background
    for h in halte_list:
        if h.get("lat") and h.get("lon"):
            _circle_marker(
                m, h["lat"], h["lon"],
                color="#9E9E9E", radius=4,
                tooltip=h["nama"],
                popup_text=f"🚏 {h['nama']} [{h['koridor']}]",
                fill_color="#BDBDBD",
            )

    if not result.ditemukan or not result.rute_id:
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                          mode="w", encoding="utf-8")
        m.save(tmp.name)
        return tmp.name

    # ── Kumpulkan koordinat rute ──
    coords_rute = []
    for hid in result.rute_id:
        h = id_ke_halte.get(hid, {})
        if h.get("lat") and h.get("lon"):
            coords_rute.append((h["lat"], h["lon"]))

    # ── Gambar jalur utama (hijau terang, via OSRM) ──
    if len(coords_rute) >= 2:
        osrm_coords = get_osrm_route(coords_rute)
        line_coords = osrm_coords if osrm_coords else coords_rute

        # Garis bayangan (hitam, lebih tebal) biar jalur terlihat jelas
        folium.PolyLine(
            locations=line_coords,
            color="#000000",
            weight=9,
            opacity=0.3,
            tooltip="Rute utama",
        ).add_to(m)

        # Jalur utama hijau terang
        folium.PolyLine(
            locations=line_coords,
            color=WARNA_JALUR_UTAMA,
            weight=6,
            opacity=0.95,
            tooltip=f"Rute: {result.nama_asal} → {result.nama_tujuan}",
            dash_array=None,
        ).add_to(m)

    # ── Node: halte yang dilewati (abu gelap, lebih besar) ──
    rute_ids_set  = set(result.rute_id)
    transit_ids   = {t.di_halte_id for t in result.transit}

    for i, hid in enumerate(result.rute_id):
        h = id_ke_halte.get(hid, {})
        if not h.get("lat"):
            continue
        lat, lon = h["lat"], h["lon"]
        nama     = h.get("nama", hid)

        if hid == result.rute_id[0]:
            # ── ASAL: hijau, besar ──
            folium.Marker(
                location=[lat, lon],
                tooltip=f"🟢 ASAL: {nama}",
                popup=folium.Popup(f"<b>🟢 ASAL</b><br>{nama}", max_width=220),
                icon=folium.Icon(color="green", icon="circle", prefix="fa"),
            ).add_to(m)

        elif hid == result.rute_id[-1]:
            # ── TUJUAN: merah, besar ──
            folium.Marker(
                location=[lat, lon],
                tooltip=f"🔴 TUJUAN: {nama}",
                popup=folium.Popup(f"<b>🔴 TUJUAN</b><br>{nama}", max_width=220),
                icon=folium.Icon(color="red", icon="flag", prefix="fa"),
            ).add_to(m)

        elif hid in transit_ids:
            # ── TRANSIT: biru ──
            t = next((t for t in result.transit if t.di_halte_id == hid), None)
            kor_info = f"Kor.{t.dari_koridor} → Kor.{t.ke_koridor}" if t else ""
            _circle_marker(
                m, lat, lon,
                color="#1565C0", radius=10,
                tooltip=f"🔵 TRANSIT: {nama}",
                popup_text=f"<b>🔵 TRANSIT</b><br>{nama}<br>{kor_info}",
                fill_color="#1E88E5",
            )

        else:
            # ── DILEWATI: abu gelap, sedang ──
            _circle_marker(
                m, lat, lon,
                color="#424242", radius=7,
                tooltip=f"● {i+1}. {nama}",
                popup_text=f"<b>{i+1}. {nama}</b><br>Koridor {h.get('koridor','')}",
                fill_color="#616161",
            )

    # ── Fit bounds ──
    if coords_rute:
        m.fit_bounds([
            [min(c[0] for c in coords_rute) - 0.01,
             min(c[1] for c in coords_rute) - 0.01],
            [max(c[0] for c in coords_rute) + 0.01,
             max(c[1] for c in coords_rute) + 0.01],
        ])

    # ── Legend sederhana di pojok kanan bawah ──
    legend_html = """
    <div style="
        position: fixed; bottom: 24px; right: 24px; z-index: 1000;
        background: rgba(20,20,40,0.88); border-radius: 10px;
        padding: 12px 16px; font-family: 'Segoe UI', sans-serif;
        font-size: 13px; color: #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        line-height: 1.8;
    ">
        <b style="font-size:14px;">🗺 Keterangan</b><br>
        <span style="color:#00E676;">━━</span> Jalur Utama<br>
        <span style="color:#4CAF50;">⬤</span> Halte Asal<br>
        <span style="color:#F44336;">⬤</span> Halte Tujuan<br>
        <span style="color:#1E88E5;">⬤</span> Titik Transit<br>
        <span style="color:#616161;">⬤</span> Halte Dilewati<br>
        <span style="color:#BDBDBD;">⬤</span> Halte Lainnya
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                      mode="w", encoding="utf-8")
    m.save(tmp.name)
    return tmp.name


# ── Worker Thread ──────────────────────────────────────────────────

class RouteWorker(QThread):
    selesai = pyqtSignal(object, str)

    def __init__(self, graph, halte_list, id_asal, id_tujuan, pelajar):
        super().__init__()
        self.graph      = graph
        self.halte_list = halte_list
        self.id_asal    = id_asal
        self.id_tujuan  = id_tujuan
        self.pelajar    = pelajar

    def run(self):
        result    = cari_rute(self.graph, self.halte_list,
                              self.id_asal, self.id_tujuan, self.pelajar)
        html_path = build_folium_map(result, self.halte_list)
        self.selesai.emit(result, html_path)


# ── Main Window ────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Balikpapan City Trans — Route Finder")
        self.setMinimumSize(1200, 720)

        self.graph      = None
        self.halte_list = []
        self.worker     = None
        self._tmp_html  = None

        self._setup_ui()
        self._load_data()

    # ── Setup UI ────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ─── Panel kiri ───────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(380)           # sedikit lebih lebar
        left.setStyleSheet("background:#1a1a2e;")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(20, 20, 20, 16)
        lv.setSpacing(14)

        # Header
        title = QLabel("🚌 Bacitra Route Finder")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))   # naik dari 14 → 16
        title.setStyleSheet("color:#e2e2e2;")
        lv.addWidget(title)

        subtitle = QLabel("Balikpapan City Trans")
        subtitle.setFont(QFont("Segoe UI", 12))             # naik dari 11 → 12
        subtitle.setStyleSheet("color:#7f8c9a;")
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
        self.chk_pelajar.setFont(QFont("Segoe UI", 13))    # naik dari 12 → 13
        self.chk_pelajar.setStyleSheet("color:#bdc3c7;")
        lv.addWidget(self.chk_pelajar)

        # Tombol cari
        self.btn_cari = QPushButton("🔍  Cari Rute")
        self.btn_cari.setFont(QFont("Segoe UI", 13, QFont.Bold))  # naik dari 12 → 13
        self.btn_cari.setFixedHeight(48)                           # naik dari 44 → 48
        self.btn_cari.setStyleSheet("""
            QPushButton {
                background: #2980b9;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover   { background: #3498db; }
            QPushButton:disabled{ background: #555; color: #888; }
        """)
        self.btn_cari.clicked.connect(self._cari_rute)
        lv.addWidget(self.btn_cari)

        lv.addWidget(self._divider())

        # Panel hasil scrollable
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:#1a1a2e; border:none;")
        self.hasil_widget  = QWidget()
        self.hasil_layout  = QVBoxLayout(self.hasil_widget)
        self.hasil_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.hasil_widget)
        lv.addWidget(self.scroll)

        # Status bar bawah
        self.lbl_status = QLabel("Memuat data...")
        self.lbl_status.setFont(QFont("Segoe UI", 11))     # naik dari 10 → 11
        self.lbl_status.setStyleSheet("color:#7f8c9a;")
        lv.addWidget(self.lbl_status)

        splitter.addWidget(left)

        # ─── Peta kanan ───────────────────────────────────────
        self.map_view = QWebEngineView()
        self.map_view.setStyleSheet("background:#0f0f1e;")
        splitter.addWidget(self.map_view)
        splitter.setSizes([380, 820])

        self._tampilkan_peta_kosong()

    # ── Widget helpers ───────────────────────────────────────────

    def _label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setFont(QFont("Segoe UI", 13, QFont.Bold))        # naik dari 12 → 13
        l.setStyleSheet("color:#bdc3c7;")
        return l

    def _combo(self) -> QComboBox:
        c = QComboBox()
        c.setEditable(True)
        c.setFixedHeight(40)                                 # naik dari 36 → 40
        c.setFont(QFont("Segoe UI", 13))                    # naik dari 12 → 13
        c.setStyleSheet("""
            QComboBox {
                background: #16213e;
                color: #e2e2e2;
                border: 1px solid #2c3e50;
                border-radius: 6px;
                padding: 4px 10px;
            }
            QComboBox QAbstractItemView {
                background: #16213e;
                color: #e2e2e2;
                font-size: 13px;
                selection-background-color: #2980b9;
            }
        """)
        return c

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background:#2c3e50; max-height:1px;")
        return line

    # ── Load data ────────────────────────────────────────────────

    def _load_data(self):
        if not os.path.exists(HALTE_JSON):
            self.lbl_status.setText("❌ halte.json tidak ditemukan!")
            return
        try:
            self.graph, self.halte_list = load_graph_dari_file(HALTE_JSON)
            self._isi_combo()
            total_edge = sum(len(v) for v in self.graph.values())
            self.lbl_status.setText(
                f"✅ {len(self.halte_list)} halte  |  {total_edge} edge"
            )
        except Exception as e:
            self.lbl_status.setText(f"❌ Error: {e}")

    def _isi_combo(self):
        items = sorted(
            [(f"{h['nama']}  [{h['koridor']}]", h["id"]) for h in self.halte_list],
            key=lambda x: x[0],
        )
        for combo in (self.combo_asal, self.combo_tujuan):
            combo.clear()
            for label, hid in items:
                combo.addItem(label, userData=hid)

    # ── Cari rute ────────────────────────────────────────────────

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

    # ── Tampilkan hasil ──────────────────────────────────────────

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
            f"⏱  Waktu tempuh  :  {result.total_waktu} menit\n"
            f"🚏  Jumlah halte   :  {result.jumlah_halte} halte\n"
            f"🛤  Koridor          :  {' → '.join(result.koridor_dipakai)}\n"
            f"💰  Biaya ({result.tipe_penumpang})  :  Rp {result.total_biaya:,}"
        )
        self._tambah_card("✅ Rute Ditemukan", ringkasan, "#27ae60")

        # Card transit
        if result.transit:
            transit_text = ""
            for t in result.transit:
                transit_text += f"🔵 Di {t.di_halte_nama}\n"
                transit_text += f"    Kor.{t.dari_koridor} → Kor.{t.ke_koridor}\n"
            self._tambah_card(
                f"🔵 Transit ({len(result.transit)}x)",
                transit_text.strip(), "#1E88E5"
            )

        # Card urutan halte
        transit_ids  = {t.di_halte_id for t in result.transit}
        urutan_text  = ""
        for i, (hid, nama) in enumerate(zip(result.rute_id, result.rute_nama)):
            if   hid == result.rute_id[0]:  prefix = "🟢"
            elif hid == result.rute_id[-1]: prefix = "🔴"
            elif hid in transit_ids:        prefix = "🔵"
            else:                           prefix = "⚫"
            urutan_text += f"{prefix} {i+1:02d}. {nama}\n"
        self._tambah_card("📍 Urutan Halte", urutan_text.strip(), "#546e7a")

        # Load peta
        if self._tmp_html:
            try:
                os.unlink(self._tmp_html)
            except Exception:
                pass
        self._tmp_html = html_path
        self.map_view.load(QUrl.fromLocalFile(html_path))

        self.lbl_status.setText(
            f"Rute: {result.nama_asal} → {result.nama_tujuan}  |  "
            f"{result.total_waktu} mnt  |  Rp {result.total_biaya:,}"
        )

    def _tambah_card(self, judul: str, isi: str, warna: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #16213e;
                border-left: 4px solid {warna};
                border-radius: 6px;
                margin-bottom: 6px;
            }}
        """)
        cv = QVBoxLayout(card)
        cv.setContentsMargins(12, 8, 12, 8)
        cv.setSpacing(5)

        lbl_judul = QLabel(judul)
        lbl_judul.setFont(QFont("Segoe UI", 13, QFont.Bold))   # naik dari 12 → 13
        lbl_judul.setStyleSheet(f"color:{warna};")
        cv.addWidget(lbl_judul)

        lbl_isi = QLabel(isi)
        lbl_isi.setFont(QFont("Segoe UI", 12))                 # naik dari 11 → 12
        lbl_isi.setStyleSheet("color:#cfd8dc;")
        lbl_isi.setWordWrap(True)
        cv.addWidget(lbl_isi)

        self.hasil_layout.addWidget(card)

    def _tampilkan_peta_kosong(self):
        m = folium.Map(location=BALIKPAPAN_CENTER, zoom_start=13)
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                          mode="w", encoding="utf-8")
        m.save(tmp.name)
        self.map_view.load(QUrl.fromLocalFile(tmp.name))


# ── Entry point ────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
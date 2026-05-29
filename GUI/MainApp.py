"""
gui/app.py
──────────
GUI PyQt5 untuk pencarian rute Balikpapan City Trans.

Revisi:
  ✅ Panel kiri lebih lebar (480px) + scroll halus
  ✅ Card info tidak terpotong — teks wrap sempurna
  ✅ Layout card pakai grid agar label & nilai sejajar rapi
  ✅ Warna node: hijau/merah/biru/abu sesuai permintaan
  ✅ Jalur utama hijau terang via OSRM
  ✅ Legend di peta
"""

import os
import sys
import json
import tempfile
import requests
import folium

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFrame, QScrollArea,
    QCheckBox, QSplitter, QSizePolicy, QGridLayout
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
WARNA_JALUR_UTAMA = "#00E676"   # hijau terang

FONT_REGULAR = QFont("Segoe UI", 13)
FONT_BOLD    = QFont("Segoe UI", 13, QFont.Bold)
FONT_TITLE   = QFont("Segoe UI", 16, QFont.Bold)
FONT_SMALL   = QFont("Segoe UI", 11)

STYLE_PANEL  = "background:#1a1a2e;"
STYLE_CARD   = "background:#16213e; border-radius:8px; margin-bottom:6px;"


# ── OSRM ──────────────────────────────────────────────────────────

def get_osrm_route(coords: list[tuple]) -> list[list] | None:
    if len(coords) < 2:
        return None
    waypoints = ";".join(f"{lon},{lat}" for lat, lon in coords)
    try:
        r = requests.get(
            f"{OSRM_URL}/{waypoints}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok":
            return [[lat, lon] for lon, lat in
                    data["routes"][0]["geometry"]["coordinates"]]
    except Exception as e:
        print(f"  ⚠️ OSRM: {e}")
    return None


def _circle(m, lat, lon, color, fill, radius, tooltip, popup):
    folium.CircleMarker(
        location=[lat, lon], radius=radius,
        color=color, fill=True, fill_color=fill,
        fill_opacity=0.92, weight=2,
        tooltip=tooltip,
        popup=folium.Popup(popup, max_width=240),
    ).add_to(m)


def build_folium_map(result: RuteResult, halte_list: list) -> str:
    id_ke_halte = {h["id"]: h for h in halte_list}

    m = folium.Map(location=BALIKPAPAN_CENTER, zoom_start=13,
                   tiles="OpenStreetMap")

    # Semua halte abu terang (background)
    for h in halte_list:
        if h.get("lat") and h.get("lon"):
            _circle(m, h["lat"], h["lon"],
                    "#9E9E9E", "#BDBDBD", 4,
                    h["nama"], f"🚏 {h['nama']} [{h['koridor']}]")

    if not result.ditemukan or not result.rute_id:
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                          mode="w", encoding="utf-8")
        m.save(tmp.name)
        return tmp.name

    # Koordinat rute
    coords_rute = []
    for hid in result.rute_id:
        h = id_ke_halte.get(hid, {})
        if h.get("lat") and h.get("lon"):
            coords_rute.append((h["lat"], h["lon"]))

    # Jalur utama hijau terang
    if len(coords_rute) >= 2:
        line = get_osrm_route(coords_rute) or coords_rute
        # Shadow
        folium.PolyLine(line, color="#000", weight=9,
                        opacity=0.25).add_to(m)
        # Jalur utama
        folium.PolyLine(line, color=WARNA_JALUR_UTAMA, weight=6,
                        opacity=0.95,
                        tooltip=f"{result.nama_asal} → {result.nama_tujuan}"
                        ).add_to(m)

    # Node rute
    transit_ids = {t.di_halte_id for t in result.transit}
    for i, hid in enumerate(result.rute_id):
        h = id_ke_halte.get(hid, {})
        if not (h.get("lat") and h.get("lon")):
            continue
        lat, lon, nama = h["lat"], h["lon"], h.get("nama", hid)

        if hid == result.rute_id[0]:
            folium.Marker(
                [lat, lon],
                tooltip=f"🟢 ASAL: {nama}",
                popup=folium.Popup(f"<b>🟢 ASAL</b><br>{nama}", max_width=240),
                icon=folium.Icon(color="green", icon="circle", prefix="fa"),
            ).add_to(m)

        elif hid == result.rute_id[-1]:
            folium.Marker(
                [lat, lon],
                tooltip=f"🔴 TUJUAN: {nama}",
                popup=folium.Popup(f"<b>🔴 TUJUAN</b><br>{nama}", max_width=240),
                icon=folium.Icon(color="red", icon="flag", prefix="fa"),
            ).add_to(m)

        elif hid in transit_ids:
            t    = next((t for t in result.transit if t.di_halte_id == hid), None)
            info = f"Kor.{t.dari_koridor} → Kor.{t.ke_koridor}" if t else ""
            _circle(m, lat, lon, "#1565C0", "#1E88E5", 10,
                    f"🔵 TRANSIT: {nama}",
                    f"<b>🔵 TRANSIT</b><br>{nama}<br>{info}")
        else:
            _circle(m, lat, lon, "#424242", "#616161", 7,
                    f"● {i+1}. {nama}",
                    f"<b>{i+1}. {nama}</b><br>Koridor {h.get('koridor','')}")

    # Fit bounds
    if coords_rute:
        m.fit_bounds([
            [min(c[0] for c in coords_rute) - 0.01,
             min(c[1] for c in coords_rute) - 0.01],
            [max(c[0] for c in coords_rute) + 0.01,
             max(c[1] for c in coords_rute) + 0.01],
        ])

    # Legend
    m.get_root().html.add_child(folium.Element("""
    <div style="position:fixed;bottom:24px;right:24px;z-index:1000;
         background:rgba(20,20,40,0.88);border-radius:10px;
         padding:12px 18px;font-family:'Segoe UI',sans-serif;
         font-size:13px;color:#eee;line-height:2;
         box-shadow:0 2px 8px rgba(0,0,0,0.4);">
      <b style="font-size:14px;">🗺 Keterangan</b><br>
      <span style="color:#00E676;">━━</span> Jalur Utama<br>
      <span style="color:#4CAF50;">⬤</span> Halte Asal<br>
      <span style="color:#F44336;">⬤</span> Halte Tujuan<br>
      <span style="color:#1E88E5;">⬤</span> Titik Transit<br>
      <span style="color:#616161;">⬤</span> Halte Dilewati<br>
      <span style="color:#BDBDBD;">⬤</span> Halte Lainnya
    </div>"""))

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                      mode="w", encoding="utf-8")
    m.save(tmp.name)
    return tmp.name


# ── Worker thread ─────────────────────────────────────────────────

class RouteWorker(QThread):
    selesai = pyqtSignal(object, str)

    def __init__(self, graph, halte_list, id_asal, id_tujuan, pelajar):
        super().__init__()
        self.graph = graph; self.halte_list = halte_list
        self.id_asal = id_asal; self.id_tujuan = id_tujuan
        self.pelajar = pelajar

    def run(self):
        result    = cari_rute(self.graph, self.halte_list,
                              self.id_asal, self.id_tujuan, self.pelajar)
        html_path = build_folium_map(result, self.halte_list)
        self.selesai.emit(result, html_path)


# ── Info Card ─────────────────────────────────────────────────────

class InfoCard(QFrame):
    """Card informasi dengan judul + grid label:nilai yang tidak terpotong."""

    def __init__(self, judul: str, warna: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: #16213e;
                border-left: 4px solid {warna};
                border-radius: 8px;
                margin-bottom: 8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(6)

        lbl = QLabel(judul)
        lbl.setFont(FONT_BOLD)
        lbl.setStyleSheet(f"color:{warna}; background:transparent;")
        outer.addWidget(lbl)

        self._grid = QGridLayout()
        self._grid.setSpacing(4)
        self._grid.setColumnStretch(1, 1)   # kolom nilai bisa melebar
        outer.addLayout(self._grid)
        self._row = 0

    def tambah_baris(self, label: str, nilai: str):
        """Tambah satu baris label : nilai."""
        lbl_k = QLabel(label)
        lbl_k.setFont(FONT_REGULAR)
        lbl_k.setStyleSheet("color:#78909C; background:transparent;")
        lbl_k.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        lbl_v = QLabel(nilai)
        lbl_v.setFont(FONT_REGULAR)
        lbl_v.setStyleSheet("color:#CFD8DC; background:transparent;")
        lbl_v.setWordWrap(True)
        lbl_v.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self._grid.addWidget(lbl_k, self._row, 0, Qt.AlignTop)
        self._grid.addWidget(lbl_v, self._row, 1, Qt.AlignTop)
        self._row += 1

    def tambah_teks(self, teks: str):
        """Tambah blok teks bebas (untuk list halte)."""
        lbl = QLabel(teks)
        lbl.setFont(FONT_REGULAR)
        lbl.setStyleSheet("color:#CFD8DC; background:transparent;")
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._grid.addWidget(lbl, self._row, 0, 1, 2)
        self._row += 1


# ── Main Window ───────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Balikpapan City Trans — Route Finder")
        self.setMinimumSize(1280, 720)
        self.graph = None; self.halte_list = []
        self.worker = None; self._tmp_html = None
        self._setup_ui()
        self._load_data()

    # ── UI ──────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ── Panel kiri (480px) ──────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(420)
        left.setMaximumWidth(520)
        left.setStyleSheet(STYLE_PANEL)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(20, 20, 20, 14)
        lv.setSpacing(12)

        # Header
        title = QLabel("🚌 Bacitra Route Finder")
        title.setFont(FONT_TITLE)
        title.setStyleSheet("color:#E2E2E2;")
        lv.addWidget(title)

        sub = QLabel("Balikpapan City Trans")
        sub.setFont(FONT_SMALL)
        sub.setStyleSheet("color:#607D8B;")
        lv.addWidget(sub)

        lv.addWidget(self._divider())

        # Form input
        lv.addWidget(self._lbl("📍 Halte Asal"))
        self.combo_asal = self._combo()
        lv.addWidget(self.combo_asal)

        lv.addWidget(self._lbl("🏁 Halte Tujuan"))
        self.combo_tujuan = self._combo()
        lv.addWidget(self.combo_tujuan)

        self.chk_pelajar = QCheckBox("Tarif Pelajar  (Rp 2.000 / koridor)")
        self.chk_pelajar.setFont(FONT_REGULAR)
        self.chk_pelajar.setStyleSheet("color:#B0BEC5;")
        lv.addWidget(self.chk_pelajar)

        self.btn_cari = QPushButton("🔍  Cari Rute")
        self.btn_cari.setFont(FONT_BOLD)
        self.btn_cari.setFixedHeight(50)
        self.btn_cari.setStyleSheet("""
            QPushButton            { background:#1565C0; color:white;
                                     border-radius:8px; border:none; }
            QPushButton:hover      { background:#1976D2; }
            QPushButton:disabled   { background:#37474F; color:#607D8B; }
        """)
        self.btn_cari.clicked.connect(self._cari_rute)
        lv.addWidget(self.btn_cari)

        lv.addWidget(self._divider())

        # ── Scroll area hasil ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea            { background:#1a1a2e; border:none; }
            QScrollBar:vertical    { background:#1a1a2e; width:6px; }
            QScrollBar::handle:vertical { background:#37474F; border-radius:3px; }
        """)
        self.hasil_widget = QWidget()
        self.hasil_widget.setStyleSheet("background:#1a1a2e;")
        self.hasil_layout = QVBoxLayout(self.hasil_widget)
        self.hasil_layout.setContentsMargins(0, 0, 4, 0)
        self.hasil_layout.setSpacing(0)
        self.hasil_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.hasil_widget)
        lv.addWidget(self.scroll, stretch=1)

        # Status
        self.lbl_status = QLabel("Memuat data...")
        self.lbl_status.setFont(FONT_SMALL)
        self.lbl_status.setStyleSheet("color:#546E7A;")
        lv.addWidget(self.lbl_status)

        splitter.addWidget(left)

        # ── Peta kanan ──────────────────────────────────────────
        self.map_view = QWebEngineView()
        splitter.addWidget(self.map_view)
        splitter.setSizes([460, 820])

        self._tampilkan_peta_kosong()

    def _lbl(self, text):
        l = QLabel(text)
        l.setFont(FONT_BOLD)
        l.setStyleSheet("color:#B0BEC5;")
        return l

    def _combo(self):
        c = QComboBox()
        c.setEditable(True)
        c.setFixedHeight(42)
        c.setFont(FONT_REGULAR)
        c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        c.setStyleSheet("""
            QComboBox {
                background:#16213e; color:#E2E2E2;
                border:1px solid #37474F; border-radius:6px;
                padding:4px 10px;
            }
            QComboBox QAbstractItemView {
                background:#16213e; color:#E2E2E2;
                selection-background-color:#1565C0;
                font-size:13px;
            }
        """)
        return c

    def _divider(self):
        f = QFrame(); f.setFrameShape(QFrame.HLine)
        f.setStyleSheet("background:#263238; max-height:1px;")
        return f

    # ── Data ────────────────────────────────────────────────────

    def _load_data(self):
        if not os.path.exists(HALTE_JSON):
            self.lbl_status.setText("❌ halte.json tidak ditemukan!")
            return
        try:
            self.graph, self.halte_list = load_graph_dari_file(HALTE_JSON)
            self._isi_combo()
            n_edge = sum(len(v) for v in self.graph.values())
            self.lbl_status.setText(
                f"✅  {len(self.halte_list)} halte  |  {n_edge} edge"
            )
        except Exception as e:
            self.lbl_status.setText(f"❌ Error: {e}")

    def _isi_combo(self):
        items = sorted(
            [(f"{h['nama']}  [{h['koridor']}]", h["id"])
             for h in self.halte_list],
            key=lambda x: x[0],
        )
        for c in (self.combo_asal, self.combo_tujuan):
            c.clear()
            for label, hid in items:
                c.addItem(label, userData=hid)

    # ── Cari ────────────────────────────────────────────────────

    def _cari_rute(self):
        if not self.graph:
            return
        id_asal   = self.combo_asal.currentData()
        id_tujuan = self.combo_tujuan.currentData()
        if not id_asal or not id_tujuan:
            self.lbl_status.setText("⚠️ Pilih halte asal dan tujuan.")
            return

        self.btn_cari.setEnabled(False)
        self.btn_cari.setText("⏳  Mencari rute...")
        self.lbl_status.setText("Menghitung rute...")

        self.worker = RouteWorker(
            self.graph, self.halte_list, id_asal, id_tujuan,
            self.chk_pelajar.isChecked()
        )
        self.worker.selesai.connect(self._tampilkan_hasil)
        self.worker.start()

    # ── Tampilkan hasil ─────────────────────────────────────────

    def _tampilkan_hasil(self, result: RuteResult, html_path: str):
        self.btn_cari.setEnabled(True)
        self.btn_cari.setText("🔍  Cari Rute")

        # Bersihkan
        for i in reversed(range(self.hasil_layout.count())):
            w = self.hasil_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not result.ditemukan:
            c = InfoCard("❌ Rute Tidak Ditemukan", "#EF5350")
            c.tambah_teks(result.pesan)
            self.hasil_layout.addWidget(c)
            self.lbl_status.setText("Rute tidak ditemukan.")
            self._tampilkan_peta_kosong()
            return

        # ── Card Ringkasan ──────────────────────────────────────
        c1 = InfoCard("✅ Ringkasan Perjalanan", "#00C853")
        c1.tambah_baris("⏱  Waktu tempuh",
                        f"{result.total_waktu} menit")
        c1.tambah_baris("🚏  Jumlah halte",
                        f"{result.jumlah_halte} halte")
        c1.tambah_baris("🛤  Koridor dipakai",
                        "  →  ".join(result.koridor_dipakai)
                        if result.koridor_dipakai else "-")
        c1.tambah_baris("🔄  Jumlah transit",
                        f"{len(result.transit)}x"
                        if result.transit else "Tidak ada transit")
        c1.tambah_baris("💰  Biaya perjalanan",
                        f"Rp {result.total_biaya:,}  ({result.tipe_penumpang})")
        if result.detail_biaya:
            c1.tambah_baris("   Detail biaya", result.detail_biaya)
        self.hasil_layout.addWidget(c1)

        # ── Card Transit ────────────────────────────────────────
        if result.transit:
            c2 = InfoCard(f"🔵 Titik Transit  ({len(result.transit)}x)",
                          "#1E88E5")
            for t in result.transit:
                c2.tambah_baris(
                    f"📍 {t.di_halte_nama}",
                    f"Koridor {t.dari_koridor}  →  Koridor {t.ke_koridor}"
                )
            self.hasil_layout.addWidget(c2)

        # ── Card Urutan Halte ───────────────────────────────────
        transit_ids = {t.di_halte_id for t in result.transit}
        c3 = InfoCard("📍 Urutan Halte yang Dilewati", "#546E7A")
        urutan = ""
        for i, (hid, nama) in enumerate(
                zip(result.rute_id, result.rute_nama)):
            if   hid == result.rute_id[0]:  ikon = "🟢"
            elif hid == result.rute_id[-1]: ikon = "🔴"
            elif hid in transit_ids:        ikon = "🔵"
            else:                           ikon = "⚫"
            urutan += f"{ikon}  {i+1:02d}.  {nama}\n"
        c3.tambah_teks(urutan.strip())
        self.hasil_layout.addWidget(c3)

        # Load peta
        if self._tmp_html:
            try: os.unlink(self._tmp_html)
            except: pass
        self._tmp_html = html_path
        self.map_view.load(QUrl.fromLocalFile(html_path))

        self.lbl_status.setText(
            f"{result.nama_asal}  →  {result.nama_tujuan}  |  "
            f"{result.total_waktu} mnt  |  Rp {result.total_biaya:,}"
        )

    def _tampilkan_peta_kosong(self):
        m   = folium.Map(location=BALIKPAPAN_CENTER, zoom_start=13)
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                          mode="w", encoding="utf-8")
        m.save(tmp.name)
        self.map_view.load(QUrl.fromLocalFile(tmp.name))


# ── Entry point ───────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Djikstra')))

from graphBuilder import load_graph_dari_file
from Djikstra import cari_rute, RuteResult

# ── Konstanta ──────────────────────────────────────────────────────
HALTE_JSON        = os.path.join(os.path.dirname(__file__), '..', "output", "halte.json")
OSRM_URL          = "http://router.project-osrm.org/route/v1/driving"
BALIKPAPAN_CENTER = [-1.270, 116.860]

WARNA_JALUR = {
    "1":  "#00E676",
    "2A": "#7C4DFF",
    "2B": "#FF6D00",
}

FONT_TITLE   = QFont("Segoe UI", 16, QFont.Bold)
FONT_BOLD    = QFont("Segoe UI", 13, QFont.Bold)
FONT_REGULAR = QFont("Segoe UI", 13)
FONT_SMALL   = QFont("Segoe UI", 11)


# ── OSRM ──────────────────────────────────────────────────────────

def get_osrm_route(coords):
    # FIX #2 (gui) — type hint list[tuple]|None tidak support Python < 3.10,
    # hapus type hint dari signature, pakai typing di dalam jika perlu.
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
            return [
                [lat, lon]
                for lon, lat in data["routes"][0]["geometry"]["coordinates"]
            ]
    except Exception as e:
        print(f"  ⚠️ OSRM: {e}")
    return None


# ── Folium Map ─────────────────────────────────────────────────────

def _div_icon(nomor, warna_bg, warna_teks="white", ukuran=28):
    return folium.DivIcon(
        html=f"""
        <div style="
            width:{ukuran}px; height:{ukuran}px;
            background:{warna_bg};
            border:2px solid white;
            border-radius:50%;
            display:flex; align-items:center; justify-content:center;
            font-family:'Segoe UI',sans-serif;
            font-size:{ukuran//2 - 1}px;
            font-weight:bold;
            color:{warna_teks};
            box-shadow:0 2px 4px rgba(0,0,0,0.4);
        ">{nomor}</div>""",
        icon_size=(ukuran, ukuran),
        icon_anchor=(ukuran // 2, ukuran // 2),
    )


def build_folium_map(result: RuteResult, halte_list: list) -> str:
    id_ke_halte = {h["id"]: h for h in halte_list}

    m = folium.Map(location=BALIKPAPAN_CENTER, zoom_start=13,
                    tiles="OpenStreetMap")

    # Semua halte (abu kecil, background)
    for h in halte_list:
        if h.get("lat") and h.get("lon"):
            folium.CircleMarker(
                location=[h["lat"], h["lon"]], radius=3,
                color="#9E9E9E", fill=True, fill_color="#BDBDBD",
                fill_opacity=0.7, weight=1,
                tooltip=h["nama"],
            ).add_to(m)

    if not result.ditemukan or not result.rute_id:
        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8")
        m.save(tmp.name)
        return tmp.name

    # Gambar jalur per segmen koridor
    transit_ids         = {t.di_halte_id for t in result.transit}
    segmen_sekarang_kor = None
    segmen_coords       = []

    def _flush_segmen(kor, coords):
        if len(coords) < 2:
            return
        warna = WARNA_JALUR.get(kor, "#607D8B")
        osrm  = get_osrm_route(coords)
        line  = osrm if osrm else coords
        folium.PolyLine(line, color="#000", weight=9, opacity=0.2).add_to(m)
        folium.PolyLine(line, color=warna, weight=6, opacity=0.95,
                        tooltip=f"Koridor {kor}").add_to(m)

    for i, hid in enumerate(result.rute_id):
        h   = id_ke_halte.get(hid, {})
        kor = result.rute_koridor[i] if i < len(result.rute_koridor) else "1"

        if not (h.get("lat") and h.get("lon")):
            continue

        coord = (h["lat"], h["lon"])

        if segmen_sekarang_kor is None:
            segmen_sekarang_kor = kor
            segmen_coords       = [coord]
        elif kor == segmen_sekarang_kor:
            segmen_coords.append(coord)
        else:
            # FIX #3 (gui) — titik transit tidak lagi ditambahkan ke segmen lama
            # sebelum flush, supaya tidak digambar dua kali di titik transit.
            _flush_segmen(segmen_sekarang_kor, segmen_coords)
            segmen_sekarang_kor = kor
            segmen_coords       = [coord]   # mulai segmen baru dari titik ini

    _flush_segmen(segmen_sekarang_kor, segmen_coords)

    # Marker tiap halte di rute
    nomor_urut = 1

    for i, hid in enumerate(result.rute_id):
        h         = id_ke_halte.get(hid, {})
        kor       = result.rute_koridor[i] if i < len(result.rute_koridor) else "1"
        warna_kor = WARNA_JALUR.get(kor, "#607D8B")

        if not (h.get("lat") and h.get("lon")):
            continue

        lat, lon = h["lat"], h["lon"]
        nama     = h.get("nama", hid)

        if hid == result.rute_id[0]:
            folium.Marker(
                [lat, lon],
                tooltip=f"🟢 1. ASAL: {nama}",
                popup=folium.Popup(
                    f"<b>🟢 ASAL</b><br>{nama}<br>Koridor {kor}", max_width=240),
                icon=_div_icon("▶", "#2E7D32", ukuran=32),
            ).add_to(m)
            nomor_urut = 2

        elif hid == result.rute_id[-1]:
            folium.Marker(
                [lat, lon],
                tooltip=f"🔴 {nomor_urut}. TUJUAN: {nama}",
                popup=folium.Popup(
                    f"<b>🔴 TUJUAN</b><br>{nama}<br>Koridor {kor}", max_width=240),
                icon=_div_icon("■", "#C62828", ukuran=32),
            ).add_to(m)

        elif hid in transit_ids:
            t    = next((t for t in result.transit if t.di_halte_id == hid), None)
            info = f"Kor.{t.dari_koridor} → Kor.{t.ke_koridor}" if t else ""
            folium.Marker(
                [lat, lon],
                tooltip=f"🔵 {nomor_urut}. TRANSIT: {nama}",
                popup=folium.Popup(
                    f"<b>🔵 TRANSIT #{nomor_urut}</b><br>{nama}<br>{info}",
                    max_width=240),
                icon=_div_icon(str(nomor_urut), "#1565C0", ukuran=30),
            ).add_to(m)
            nomor_urut += 1

        else:
            folium.Marker(
                [lat, lon],
                tooltip=f"● {nomor_urut}. {nama}",
                popup=folium.Popup(
                    f"<b>Halte #{nomor_urut}</b><br>{nama}<br>Koridor {kor}",
                    max_width=240),
                icon=_div_icon(str(nomor_urut), warna_kor, ukuran=24),
            ).add_to(m)
            nomor_urut += 1

    # Fit bounds
    coords_rute = [
        (id_ke_halte[hid]["lat"], id_ke_halte[hid]["lon"])
        for hid in result.rute_id
        if id_ke_halte.get(hid, {}).get("lat")
    ]
    if coords_rute:
        m.fit_bounds([
            [min(c[0] for c in coords_rute) - 0.01,
                min(c[1] for c in coords_rute) - 0.01],
            [max(c[0] for c in coords_rute) + 0.01,
                max(c[1] for c in coords_rute) + 0.01],
        ])

    # Legend
    legend_items = "".join(
        f'<div><span style="color:{w};font-size:16px;">━━</span> Koridor {k}</div>'
        for k, w in WARNA_JALUR.items()
    )
    m.get_root().html.add_child(folium.Element(f"""
    <div style="position:fixed;bottom:24px;right:24px;z-index:1000;
        background:rgba(20,20,40,0.9);border-radius:10px;
        padding:12px 18px;font-family:'Segoe UI',sans-serif;
        font-size:13px;color:#eee;line-height:2;
        box-shadow:0 2px 8px rgba(0,0,0,0.5);">
    <b style="font-size:14px;">🗺 Keterangan</b><br>
    {legend_items}
    <div><span style="color:#2E7D32;font-size:16px;">⬤</span> Halte Asal</div>
    <div><span style="color:#C62828;font-size:16px;">⬤</span> Halte Tujuan</div>
    <div><span style="color:#1565C0;font-size:16px;">⬤</span> Titik Transit</div>
    <div><span style="color:#607D8B;font-size:16px;">⬤</span> Halte Dilewati</div>
    <div><span style="color:#BDBDBD;font-size:12px;">⬤</span> Halte Lainnya</div>
    </div>"""))

    tmp = tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8")
    m.save(tmp.name)
    return tmp.name


# ── Worker Thread ─────────────────────────────────────────────────

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


# ── Info Card ─────────────────────────────────────────────────────

class InfoCard(QFrame):
    def __init__(self, judul: str, warna: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background:#16213e;
                border-left:4px solid {warna};
                border-radius:8px;
                margin-bottom:8px;
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
        self._grid.setColumnStretch(1, 1)
        outer.addLayout(self._grid)
        self._row = 0

    def tambah_baris(self, label: str, nilai: str):
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
        self.graph      = None
        self.halte_list = []
        self.worker     = None
        self._tmp_html  = None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # Panel kiri
        left = QWidget()
        left.setMinimumWidth(420)
        left.setMaximumWidth(520)
        left.setStyleSheet("background:#1a1a2e;")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(20, 20, 20, 14)
        lv.setSpacing(12)

        title = QLabel("🚌 Bacitra Route Finder")
        title.setFont(FONT_TITLE)
        title.setStyleSheet("color:#E2E2E2;")
        lv.addWidget(title)

        sub = QLabel("Balikpapan City Trans")
        sub.setFont(FONT_SMALL)
        sub.setStyleSheet("color:#607D8B;")
        lv.addWidget(sub)

        lv.addWidget(self._divider())

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
            QPushButton          { background:#1565C0; color:white;
                                    border-radius:8px; border:none; }
            QPushButton:hover    { background:#1976D2; }
            QPushButton:disabled { background:#37474F; color:#607D8B; }
        """)
        self.btn_cari.clicked.connect(self._cari_rute)
        lv.addWidget(self.btn_cari)

        lv.addWidget(self._divider())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea              { background:#1a1a2e; border:none; }
            QScrollBar:vertical      { background:#1a1a2e; width:6px; }
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

        self.lbl_status = QLabel("Memuat data...")
        self.lbl_status.setFont(FONT_SMALL)
        self.lbl_status.setStyleSheet("color:#546E7A;")
        lv.addWidget(self.lbl_status)

        splitter.addWidget(left)

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
            QComboBox { background:#16213e; color:#E2E2E2;
                        border:1px solid #37474F; border-radius:6px;
                        padding:4px 10px; }
            QComboBox QAbstractItemView { background:#16213e; color:#E2E2E2;
                        selection-background-color:#1565C0; font-size:13px; }
        """)
        return c

    def _divider(self):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet("background:#263238; max-height:1px;")
        return f

    def _load_data(self):
        if not os.path.exists(HALTE_JSON):
            self.lbl_status.setText("❌ output/halte.json tidak ditemukan!")
            return
        try:
            # FIX #1 (gui) terapkan — pakai load_graph_dari_file langsung,
            # bukan Djikstra.graphBuilder.load_graph_dari_file
            self.graph, self.halte_list = load_graph_dari_file(HALTE_JSON)
            self._isi_combo()
            n_edge = sum(len(v) for v in self.graph.values())
            self.lbl_status.setText(
                f"✅  {len(self.halte_list)} halte  |  {n_edge} edge")
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

    def _tampilkan_hasil(self, result: RuteResult, html_path: str):
        self.btn_cari.setEnabled(True)
        self.btn_cari.setText("🔍  Cari Rute")

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

        # Card Ringkasan
        c1 = InfoCard("✅ Ringkasan Perjalanan", "#00C853")
        c1.tambah_baris("⏱  Estimasi Waktu Tempuh ", f"{result.total_waktu} menit")
        c1.tambah_baris("🚏  Jumlah halte", f"{result.jumlah_halte} halte")
        c1.tambah_baris("🛤  Koridor",
                        "  →  ".join(result.koridor_dipakai) or "-")
        c1.tambah_baris("🔄  Transit",
                        f"{len(result.transit)}x" if result.transit
                        else "Tidak ada transit")
        c1.tambah_baris("💰  Biaya",
                        f"Rp {result.total_biaya:,}  ({result.tipe_penumpang})")
        if result.detail_biaya:
            c1.tambah_baris("   Detail", result.detail_biaya)
        self.hasil_layout.addWidget(c1)

        # Card Transit
        if result.transit:
            c2 = InfoCard(f"🔵 Titik Transit  ({len(result.transit)}x)",
                        "#1E88E5")
            for t in result.transit:
                c2.tambah_baris(
                    f"📍 {t.di_halte_nama}",
                    f"Koridor {t.dari_koridor}  →  Koridor {t.ke_koridor}"
                )
            self.hasil_layout.addWidget(c2)

        # Card Urutan Halte
        transit_ids = {t.di_halte_id for t in result.transit}
        c3 = InfoCard("📍 Urutan Halte", "#546E7A")
        nomor  = 1
        urutan = ""
        for i, (hid, nama) in enumerate(
                zip(result.rute_id, result.rute_nama)):
            kor = result.rute_koridor[i] if i < len(result.rute_koridor) else "1"
            if   hid == result.rute_id[0]:  ikon = "🟢"
            elif hid == result.rute_id[-1]: ikon = "🔴"
            elif hid in transit_ids:        ikon = "🔵"
            else:                           ikon = "⚫"
            urutan += f"{ikon} {nomor:02d}.  {nama}  [Kor.{kor}]\n"
            nomor  += 1
        c3.tambah_teks(urutan.strip())
        self.hasil_layout.addWidget(c3)

        # Load peta
        if self._tmp_html:
            try:
                os.unlink(self._tmp_html)
            except Exception:
                pass
        self._tmp_html = html_path
        self.map_view.load(QUrl.fromLocalFile(html_path))

        self.lbl_status.setText(
            f"{result.nama_asal}  →  {result.nama_tujuan}  |  "
            f"{result.total_waktu} mnt  |  Rp {result.total_biaya:,}"
        )

    def _tampilkan_peta_kosong(self):
        m   = folium.Map(location=BALIKPAPAN_CENTER, zoom_start=13)
        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8")
        m.save(tmp.name)
        self.map_view.load(QUrl.fromLocalFile(tmp.name))

    # FIX #4 (gui) — bersihkan file HTML sementara saat aplikasi ditutup
    def closeEvent(self, event):
        if self._tmp_html:
            try:
                os.unlink(self._tmp_html)
            except Exception:
                pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
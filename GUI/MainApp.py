"""
gui/app.py
──────────
GUI PyQt5 untuk pencarian rute Balikpapan City Trans (Bacitra).
"""

import os, sys, json, math, tempfile, requests, folium

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFrame, QScrollArea,
    QCheckBox, QSplitter, QSizePolicy, QGridLayout,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore  import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtGui   import QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Djikstra.graphBuilder import load_graph_dari_file, haversine
from Djikstra.Djikstra     import cari_rute, RuteResult

# ─────────────────────────────────────────────────────────────
# Konstanta tampilan
# ─────────────────────────────────────────────────────────────
HALTE_JSON        = os.path.join(os.path.dirname(__file__), "..", "output", "halte.json")
OSRM_BASE         = "http://router.project-osrm.org/route/v1/driving"
BALIKPAPAN_CENTER = [-1.270, 116.860]

# Palet warna (dark navy)
C_BG     = "#0f1923"
C_PANEL  = "#141e2b"
C_CARD   = "#1a2637"
C_BORDER = "#243447"
C_TEXT   = "#e2e8f0"
C_MUTED  = "#64748b"
C_ACCENT = "#3b82f6"
C_GREEN  = "#22c55e"
C_RED    = "#ef4444"
C_BLUE   = "#60a5fa"
C_YELLOW = "#f59e0b"
C_PURPLE = "#a78bfa"
C_TEAL   = "#2dd4bf"

WARNA_KOR = {"1": C_GREEN, "2A": C_PURPLE, "2B": C_TEAL}

FONT_TITLE = QFont("Segoe UI", 15, QFont.Bold)
FONT_BOLD  = QFont("Segoe UI", 12, QFont.Bold)
FONT_REG   = QFont("Segoe UI", 12)
FONT_SMALL = QFont("Segoe UI", 10)
FONT_MONO  = QFont("Consolas",  11)


# ─────────────────────────────────────────────────────────────
# OSRM + fallback polyline berurutan
# ─────────────────────────────────────────────────────────────

def _snap_to_road(lat: float, lon: float) -> tuple[float, float]:
    """
    Snap satu koordinat ke jalan terdekat via OSRM nearest API.
    Fallback ke koordinat asli jika gagal.
    """
    try:
        r = requests.get(
            f"http://router.project-osrm.org/nearest/v1/driving/{lon},{lat}",
            params={"number": 1},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok":
            loc = data["waypoints"][0]["location"]
            return loc[1], loc[0]   # lat, lon
    except Exception:
        pass
    return lat, lon


def get_osrm_route(coords: list[tuple]) -> list[list] | None:
    """
    Ambil geometri jalan nyata dari OSRM.
    Koordinat di-snap ke jalan terlebih dahulu agar tidak masuk gang.
    Fallback None jika gagal.
    """
    if len(coords) < 2:
        return None

    # Snap setiap titik ke jalan terdekat
    snapped = [_snap_to_road(lat, lon) for lat, lon in coords]

    waypoints = ";".join(f"{lon},{lat}" for lat, lon in snapped)
    try:
        r = requests.get(
            f"{OSRM_BASE}/{waypoints}",
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
        print(f"  ⚠️ OSRM error: {e}")
    return None


def _polyline_berurutan(coords: list[tuple]) -> list[list]:
    """
    Fallback: polyline yang menghubungkan semua titik koordinat
    secara berurutan (bukan garis lurus A→Z langsung).
    Lebih aman daripada garis lurus saat OSRM tidak tersedia.
    """
    return [[lat, lon] for lat, lon in coords]


# ─────────────────────────────────────────────────────────────
# Folium map builder
# ─────────────────────────────────────────────────────────────

def _circle(m, lat, lon, color, fill, radius, tooltip, popup_html):
    folium.CircleMarker(
        location     = [lat, lon],
        radius       = radius,
        color        = color,
        fill         = True,
        fill_color   = fill,
        fill_opacity = 0.92,
        weight       = 2,
        tooltip      = tooltip,
        popup        = folium.Popup(popup_html, max_width=280),
    ).add_to(m)


def build_folium_map(result: RuteResult, halte_list: list) -> tuple[str, float]:
    """
    Bangun peta Folium dari RuteResult.
    Returns (path_html, total_km).
    """
    id_ke_halte = {h["id"]: h for h in halte_list}

    m = folium.Map(
        location   = BALIKPAPAN_CENTER,
        zoom_start = 13,
        tiles      = "CartoDB dark_matter",
    )

    # ── Semua halte sebagai titik latar ───────────────────────
    for h in halte_list:
        if h.get("lat") and h.get("lon"):
            wk = WARNA_KOR.get(h["koridor"], C_MUTED)
            _circle(
                m, h["lat"], h["lon"],
                "#334155", wk, 3,
                f"🚏 {h['nama']} [Kor.{h['koridor']}]",
                f"<b>{h['nama']}</b><br>Koridor {h['koridor']}<br>"
                f"<small style='color:#94a3b8'>ID: {h['id']}</small>",
            )

    if not result.ditemukan or not result.rute_id:
        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8")
        m.save(tmp.name)
        return tmp.name, 0.0

    # ── Koordinat halte rute (yang punya lat/lon) ─────────────
    coords_rute: list[tuple] = []
    for hid in result.rute_id:
        h = id_ke_halte.get(hid, {})
        if h.get("lat") and h.get("lon"):
            coords_rute.append((h["lat"], h["lon"]))

    # ── Gambar jalur ──────────────────────────────────────────
    if len(coords_rute) >= 2:
        line = get_osrm_route(coords_rute) or _polyline_berurutan(coords_rute)

        # Shadow
        folium.PolyLine(line, color="#000", weight=10, opacity=0.3).add_to(m)
        # Jalur utama
        folium.PolyLine(
            line, color="#00e676", weight=5, opacity=0.95,
            tooltip=(
                f"🚌 {result.nama_asal} → {result.nama_tujuan} | "
                f"~{result.total_km:.1f} km | "
                f"{result.total_waktu} menit"
            ),
        ).add_to(m)

    # ── Node rute ─────────────────────────────────────────────
    transit_ids = {t.di_halte_id for t in result.transit}

    for i, hid in enumerate(result.rute_id):
        h = id_ke_halte.get(hid, {})
        if not (h.get("lat") and h.get("lon")):
            continue

        lat  = h["lat"]
        lon  = h["lon"]
        nama = h.get("nama", hid)
        kor  = h.get("koridor", "")
        no   = i + 1

        # Cari info jarak ke halte ini
        seg_info = ""
        if result.segmen_km:
            seg = next(
                (s for s in result.segmen_km if s["ke"] == nama), None
            )
            if seg:
                seg_info = f"<br><small>Jarak dari {seg['dari']}: {seg['km']} km</small>"

        if hid == result.rute_id[0]:
            folium.Marker(
                [lat, lon],
                tooltip = f"🟢 ASAL: {nama}",
                popup   = folium.Popup(
                    f"<b style='color:{C_GREEN}'>🟢 ASAL</b><br>"
                    f"<b>{nama}</b><br>Koridor {kor}{seg_info}",
                    max_width=280,
                ),
                icon = folium.Icon(color="green", icon="home", prefix="fa"),
            ).add_to(m)

        elif hid == result.rute_id[-1]:
            folium.Marker(
                [lat, lon],
                tooltip = f"🔴 TUJUAN: {nama}",
                popup   = folium.Popup(
                    f"<b style='color:{C_RED}'>🔴 TUJUAN</b><br>"
                    f"<b>{nama}</b><br>Koridor {kor}{seg_info}",
                    max_width=280,
                ),
                icon = folium.Icon(color="red", icon="flag", prefix="fa"),
            ).add_to(m)

        elif hid in transit_ids:
            t    = next((t for t in result.transit if t.di_halte_id == hid), None)
            info = f"Kor.{t.dari_koridor} → Kor.{t.ke_koridor}" if t else ""
            _circle(
                m, lat, lon, "#1d4ed8", "#3b82f6", 11,
                f"🔵 TRANSIT ({no}): {nama}",
                f"<b style='color:{C_BLUE}'>🔵 TRANSIT</b><br>"
                f"<b>{nama}</b><br>{info}{seg_info}",
            )

        else:
            _circle(
                m, lat, lon, "#475569", "#94a3b8", 7,
                f"● {no}. {nama}",
                f"<b>{no}. {nama}</b><br>Koridor {kor}{seg_info}",
            )

    # ── Fit bounds ────────────────────────────────────────────
    if len(coords_rute) >= 2:
        lats = [c[0] for c in coords_rute]
        lons = [c[1] for c in coords_rute]
        m.fit_bounds([
            [min(lats) - 0.01, min(lons) - 0.01],
            [max(lats) + 0.01, max(lons) + 0.01],
        ])

    # ── Legend ────────────────────────────────────────────────
    m.get_root().html.add_child(folium.Element(f"""
    <div style="
        position:fixed; bottom:20px; right:20px; z-index:1000;
        background:rgba(15,25,35,0.93);
        border:1px solid #243447; border-radius:10px;
        padding:12px 16px;
        font-family:'Segoe UI',sans-serif;
        font-size:12px; color:#e2e8f0; line-height:2;
        box-shadow:0 4px 12px rgba(0,0,0,0.5);">
    <div style="font-weight:700;font-size:13px;margin-bottom:2px;">🗺 Keterangan</div>
    <div><span style="color:#00e676;font-weight:bold;">━━━</span> Jalur Rute</div>
    <div><span style="color:{C_GREEN};">⬤</span> Halte Asal</div>
    <div><span style="color:{C_RED};">⬤</span> Halte Tujuan</div>
    <div><span style="color:{C_BLUE};">⬤</span> Titik Transit</div>
    <div><span style="color:#94a3b8;">⬤</span> Halte Dilewati</div>
    <hr style="border-color:#243447;margin:4px 0;">
    <div style="color:#64748b;font-size:11px;">Klik halte untuk detail</div>
    </div>"""))

    tmp = tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8")
    m.save(tmp.name)
    return tmp.name, result.total_km


# ─────────────────────────────────────────────────────────────
# Worker thread
# ─────────────────────────────────────────────────────────────

class RouteWorker(QThread):
    selesai = pyqtSignal(object, str, float)

    def __init__(self, graph, halte_list, id_asal, id_tujuan, pelajar):
        super().__init__()
        self.graph      = graph
        self.halte_list = halte_list
        self.id_asal    = id_asal
        self.id_tujuan  = id_tujuan
        self.pelajar    = pelajar

    def run(self):
        result          = cari_rute(self.graph, self.halte_list,
                                    self.id_asal, self.id_tujuan, self.pelajar)
        html_path, km   = build_folium_map(result, self.halte_list)
        self.selesai.emit(result, html_path, km)


# ─────────────────────────────────────────────────────────────
# Widget InfoCard
# ─────────────────────────────────────────────────────────────

class InfoCard(QFrame):
    def __init__(self, judul: str, warna: str = C_ACCENT, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background   : {C_CARD};
                border-left  : 4px solid {warna};
                border-radius: 8px;
                margin-bottom: 6px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(5)

        lbl = QLabel(judul)
        lbl.setFont(FONT_BOLD)
        lbl.setStyleSheet(f"color:{warna}; background:transparent;")
        outer.addWidget(lbl)

        self._grid = QGridLayout()
        self._grid.setSpacing(3)
        self._grid.setColumnStretch(1, 1)
        outer.addLayout(self._grid)
        self._row = 0

    def baris(self, label: str, nilai: str, warna_nilai: str = C_TEXT):
        lk = QLabel(label)
        lk.setFont(FONT_SMALL)
        lk.setStyleSheet(f"color:{C_MUTED}; background:transparent;")
        lk.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lk.setFixedWidth(115)

        lv = QLabel(nilai)
        lv.setFont(FONT_REG)
        lv.setStyleSheet(f"color:{warna_nilai}; background:transparent;")
        lv.setWordWrap(True)
        lv.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self._grid.addWidget(lk, self._row, 0, Qt.AlignTop)
        self._grid.addWidget(lv, self._row, 1, Qt.AlignTop)
        self._row += 1

    def blok(self, teks: str, font=None, warna: str = C_TEXT):
        lv = QLabel(teks)
        lv.setFont(font or FONT_MONO)
        lv.setStyleSheet(f"color:{warna}; background:transparent;")
        lv.setWordWrap(True)
        lv.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._grid.addWidget(lv, self._row, 0, 1, 2)
        self._row += 1


# ─────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Balikpapan City Trans — Bacitra Route Finder")
        self.setMinimumSize(1300, 740)
        self.graph      = None
        self.halte_list = []
        self.worker     = None
        self._tmp_html  = None
        self._setup_ui()
        self._load_data()

    # ── Setup UI ──────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background:{C_BG};")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background:{C_BORDER}; }}")
        root.addWidget(splitter)

        # ── Panel kiri ────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(400)
        left.setMaximumWidth(500)
        left.setStyleSheet(f"background:{C_PANEL};")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(20, 20, 20, 14)
        lv.setSpacing(10)

        # Header
        title = QLabel("🚌 Bacitra Route Finder")
        title.setFont(FONT_TITLE)
        title.setStyleSheet(f"color:{C_TEXT};")
        lv.addWidget(title)

        sub = QLabel("Balikpapan City Trans — Cari Rute Tercepat")
        sub.setFont(FONT_SMALL)
        sub.setStyleSheet(f"color:{C_MUTED};")
        lv.addWidget(sub)

        lv.addWidget(self._divider())

        # Form
        lv.addWidget(self._lbl("📍  Halte Asal"))
        self.combo_asal = self._combo()
        lv.addWidget(self.combo_asal)

        lv.addWidget(self._lbl("🏁  Halte Tujuan"))
        self.combo_tujuan = self._combo()
        lv.addWidget(self.combo_tujuan)

        self.chk_pelajar = QCheckBox("  Tarif Pelajar  (Rp 2.000 / koridor)")
        self.chk_pelajar.setFont(FONT_REG)
        self.chk_pelajar.setStyleSheet(f"color:{C_MUTED};")
        lv.addWidget(self.chk_pelajar)

        self.btn_cari = QPushButton("🔍   Cari Rute")
        self.btn_cari.setFont(FONT_BOLD)
        self.btn_cari.setFixedHeight(48)
        self.btn_cari.setCursor(Qt.PointingHandCursor)
        self.btn_cari.setStyleSheet(f"""
            QPushButton          {{ background:{C_ACCENT}; color:#fff;
                                    border-radius:8px; border:none; }}
            QPushButton:hover    {{ background:#2563eb; }}
            QPushButton:disabled {{ background:#1e3a5f; color:{C_MUTED}; }}
        """)
        self.btn_cari.clicked.connect(self._cari_rute)
        lv.addWidget(self.btn_cari)

        lv.addWidget(self._divider())

        # Scroll hasil
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea               {{ background:{C_PANEL}; border:none; }}
            QScrollBar:vertical       {{ background:{C_PANEL}; width:5px; }}
            QScrollBar::handle:vertical {{ background:#334155; border-radius:3px; }}
        """)
        self.hasil_widget = QWidget()
        self.hasil_widget.setStyleSheet(f"background:{C_PANEL};")
        self.hasil_layout = QVBoxLayout(self.hasil_widget)
        self.hasil_layout.setContentsMargins(0, 0, 4, 0)
        self.hasil_layout.setSpacing(4)
        self.hasil_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.hasil_widget)
        lv.addWidget(self.scroll, stretch=1)

        self.lbl_status = QLabel("⏳ Memuat data...")
        self.lbl_status.setFont(FONT_SMALL)
        self.lbl_status.setStyleSheet(f"color:{C_MUTED};")
        self.lbl_status.setWordWrap(True)
        lv.addWidget(self.lbl_status)

        splitter.addWidget(left)

        # ── Peta kanan ────────────────────────────────────────
        self.map_view = QWebEngineView()
        self.map_view.setStyleSheet(f"background:{C_BG};")
        splitter.addWidget(self.map_view)
        splitter.setSizes([440, 860])

        self._tampilkan_peta_kosong()

    def _lbl(self, text):
        l = QLabel(text)
        l.setFont(FONT_BOLD)
        l.setStyleSheet(f"color:{C_MUTED};")
        return l

    def _combo(self):
        c = QComboBox()
        c.setEditable(True)
        c.setFixedHeight(40)
        c.setFont(FONT_REG)
        c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        c.setInsertPolicy(QComboBox.NoInsert)
        c.setStyleSheet(f"""
            QComboBox {{
                background:{C_CARD}; color:{C_TEXT};
                border:1px solid {C_BORDER}; border-radius:6px;
                padding:4px 10px;
            }}
            QComboBox:focus {{ border:1px solid {C_ACCENT}; }}
            QComboBox QAbstractItemView {{
                background:{C_CARD}; color:{C_TEXT};
                selection-background-color:{C_ACCENT};
                border:1px solid {C_BORDER}; font-size:12px;
            }}
        """)
        return c

    def _divider(self):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet(f"background:{C_BORDER};")
        return f

    def _clear_hasil(self):
        for i in reversed(range(self.hasil_layout.count())):
            w = self.hasil_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

    # ── Load data ─────────────────────────────────────────────

    def _load_data(self):
        if not os.path.exists(HALTE_JSON):
            self.lbl_status.setText("❌ output/halte.json tidak ditemukan!")
            return
        try:
            self.graph, self.halte_list = load_graph_dari_file(HALTE_JSON)
            self._isi_combo()
            n_edge = sum(len(v) for v in self.graph.values())
            self.lbl_status.setText(
                f"✅  {len(self.halte_list)} halte  |  {n_edge} edge  |  siap"
            )
        except Exception as e:
            self.lbl_status.setText(f"❌ Error: {e}")

    def _isi_combo(self):
        items = sorted(
            [(f"[Kor.{h['koridor']}]  {h['nama']}", h["id"])
            for h in self.halte_list],
        )
        for c in (self.combo_asal, self.combo_tujuan):
            c.clear()
            c.addItem("— Ketik atau pilih halte —", userData=None)
            for label, hid in items:
                c.addItem(label, userData=hid)

    # ── Cari rute ─────────────────────────────────────────────

    def _cari_rute(self):
        if not self.graph:
            return
        id_asal   = self.combo_asal.currentData()
        id_tujuan = self.combo_tujuan.currentData()
        if not id_asal or not id_tujuan:
            self.lbl_status.setText("⚠️  Pilih halte asal dan tujuan terlebih dahulu.")
            return

        self.btn_cari.setEnabled(False)
        self.btn_cari.setText("⏳   Menghitung rute...")
        self.lbl_status.setText("Menjalankan Dijkstra + memuat peta...")
        self._clear_hasil()

        c = InfoCard("⏳  Sedang menghitung...", C_YELLOW)
        c.blok("Mohon tunggu sebentar.", font=FONT_REG, warna=C_MUTED)
        self.hasil_layout.addWidget(c)

        self.worker = RouteWorker(
            self.graph, self.halte_list,
            id_asal, id_tujuan,
            self.chk_pelajar.isChecked(),
        )
        self.worker.selesai.connect(self._tampilkan_hasil)
        self.worker.start()

    # ── Tampilkan hasil ───────────────────────────────────────

    def _tampilkan_hasil(self, result: RuteResult, html_path: str, km: float):
        self.btn_cari.setEnabled(True)
        self.btn_cari.setText("🔍   Cari Rute")
        self._clear_hasil()

        # Rute tidak ditemukan
        if not result.ditemukan:
            c = InfoCard("❌  Rute Tidak Ditemukan", C_RED)
            c.blok(result.pesan, font=FONT_REG, warna=C_RED)
            self.hasil_layout.addWidget(c)
            self.lbl_status.setText("Rute tidak ditemukan.")
            self._tampilkan_peta_kosong()
            return

        # ── Peringatan rute memutar ───────────────────────────
        if result.pesan:
            cw = InfoCard("⚠️  Perhatian", C_YELLOW)
            cw.blok(result.pesan, font=FONT_REG, warna=C_YELLOW)
            self.hasil_layout.addWidget(cw)

        # ── Card ringkasan ────────────────────────────────────
        c1 = InfoCard("✅  Ringkasan Perjalanan", C_GREEN)
        c1.baris("⏱ Waktu",
                f"{result.total_waktu} menit", C_TEXT)
        c1.baris("📏 Jarak",
                f"~{result.total_km:.1f} km (estimasi lurus)", C_TEXT)
        c1.baris("🚏 Halte dilalui",
                f"{result.jumlah_halte} halte", C_TEXT)
        c1.baris("🔄 Transit",
                f"{len(result.transit)}x transit"
                if result.transit else "Tidak ada (1 koridor langsung)",
                C_TEXT)
        c1.baris("🛤 Koridor",
                "  →  ".join(
                    f"Kor.{k}" for k in result.koridor_dipakai
                ) if result.koridor_dipakai else "-",
                C_TEXT)
        c1.baris("💰 Biaya",
                f"Rp {result.total_biaya:,}  ({result.tipe_penumpang})",
                C_YELLOW)
        if result.detail_biaya:
            c1.baris("   Rincian", result.detail_biaya, C_MUTED)
        self.hasil_layout.addWidget(c1)

        # ── Card titik transit ────────────────────────────────
        if result.transit:
            c2 = InfoCard(f"🔵  Titik Transit  ({len(result.transit)}x)", C_BLUE)
            for i, t in enumerate(result.transit, 1):
                c2.baris(
                    f"  {i}. {t.di_halte_nama}",
                    f"Kor.{t.dari_koridor}  →  Kor.{t.ke_koridor}",
                    C_BLUE,
                )
            self.hasil_layout.addWidget(c2)

        # ── Card jarak per segmen ─────────────────────────────
        if result.segmen_km:
            c4 = InfoCard("📏  Jarak Antar Halte", C_MUTED)
            total_disp = 0.0
            for s in result.segmen_km:
                total_disp += s["km"]
                c4.baris(
                    f"  → {s['ke']}",
                    f"{s['km']:.2f} km  (kumulatif: ~{total_disp:.2f} km)",
                    C_MUTED,
                )
            self.hasil_layout.addWidget(c4)

        # ── Card urutan halte per koridor ─────────────────────
        c3 = InfoCard("📍  Urutan Halte yang Dilewati", C_MUTED)
        transit_ids = {t.di_halte_id for t in result.transit}
        halte_info  = {h["id"]: h for h in self.halte_list}

        teks      = ""
        kor_aktif = None
        IKON_KOR  = {"1": "🟩", "2A": "🟪", "2B": "🟦"}

        for i, (hid, nama) in enumerate(
                zip(result.rute_id, result.rute_nama)):
            kor = halte_info.get(hid, {}).get("koridor", "?")
            if kor != kor_aktif:
                if kor_aktif is not None:
                    teks += "\n"
                teks += f"{IKON_KOR.get(kor,'⬜')} ─── Koridor {kor} ───\n"
                kor_aktif = kor

            if   hid == result.rute_id[0]:   ikon = "🟢"
            elif hid == result.rute_id[-1]:  ikon = "🔴"
            elif hid in transit_ids:         ikon = "🔵"
            else:                            ikon = "  ○"

            teks += f"  {ikon} {i+1:02d}. {nama}\n"

        c3.blok(teks.strip())
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
            f"✅  {result.nama_asal}  →  {result.nama_tujuan}  |  "
            f"{result.total_waktu} mnt  |  ~{result.total_km:.1f} km  |  "
            f"Rp {result.total_biaya:,}"
        )

    # ── Peta kosong (semua halte) ─────────────────────────────

    def _tampilkan_peta_kosong(self):
        m = folium.Map(
            location   = BALIKPAPAN_CENTER,
            zoom_start = 13,
            tiles      = "CartoDB dark_matter",
        )
        for h in self.halte_list:
            if h.get("lat") and h.get("lon"):
                wk = WARNA_KOR.get(h["koridor"], C_MUTED)
                _circle(
                    m, h["lat"], h["lon"], "#334155", wk, 4,
                    f"🚏 {h['nama']} [Kor.{h['koridor']}]",
                    f"<b>{h['nama']}</b><br>Koridor {h['koridor']}",
                )

        m.get_root().html.add_child(folium.Element(f"""
        <div style="
            position:fixed; bottom:20px; right:20px; z-index:1000;
            background:rgba(15,25,35,0.92);
            border:1px solid #243447; border-radius:10px;
            padding:12px 16px;
            font-family:'Segoe UI',sans-serif;
            font-size:12px; color:#e2e8f0; line-height:2;
            box-shadow:0 4px 12px rgba(0,0,0,0.5);">
        <b style="font-size:13px;">🗺 Semua Halte Bacitra</b><br>
        <span style="color:{C_GREEN};">⬤</span> Koridor 1<br>
        <span style="color:{C_PURPLE};">⬤</span> Koridor 2A<br>
        <span style="color:{C_TEAL};">⬤</span> Koridor 2B
        </div>"""))

        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8")
        m.save(tmp.name)
        self.map_view.load(QUrl.fromLocalFile(tmp.name))


# ─────────────────────────────────────────────────────────────
# Entry point (dipakai juga oleh mainapp.py)
# ─────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
"""
gui/app.py
──────────
GUI PyQt5 untuk pencarian rute Balikpapan City Trans (Bacitra).

Perbaikan dari versi sebelumnya:
  ✅ Panel kiri: combo box lebih intuitif dengan placeholder
  ✅ Info hasil: card lebih rapi, jarak estimasi ditampilkan
  ✅ Urutan halte: dibagi per segmen koridor, ada header koridor
  ✅ Peta: semua halte rute punya tooltip nomor urut
  ✅ Peta: garis rute menggunakan OSRM (fallback garis lurus)
  ✅ Peta: animasi loading saat menghitung rute
  ✅ Warna node: hijau asal, merah tujuan, biru transit, abu lewat
  ✅ Thread terpisah agar GUI tidak freeze saat hitung rute
"""

import os, sys, json, math, tempfile, requests, folium

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFrame, QScrollArea,
    QCheckBox, QSplitter, QSizePolicy, QGridLayout, QSpacerItem,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore  import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtGui   import QFont, QColor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Djikstra.graphBuilder import load_graph_dari_file
from Djikstra.Djikstra     import cari_rute, RuteResult

# ─────────────────────────────────────────────
# Konstanta
# ─────────────────────────────────────────────
HALTE_JSON        = os.path.join(os.path.dirname(__file__), "..", "output", "halte.json")
OSRM_URL          = "http://router.project-osrm.org/route/v1/driving"
BALIKPAPAN_CENTER = [-1.270, 116.860]

# Warna tema (dark navy)
C_BG        = "#0f1923"   # background utama
C_PANEL     = "#141e2b"   # panel kiri
C_CARD      = "#1a2637"   # card
C_BORDER    = "#243447"   # border card
C_TEXT      = "#e2e8f0"   # teks utama
C_MUTED     = "#64748b"   # teks redup
C_ACCENT    = "#3b82f6"   # biru aksen (tombol, link)
C_GREEN     = "#22c55e"   # asal / sukses
C_RED       = "#ef4444"   # tujuan / error
C_BLUE      = "#60a5fa"   # transit
C_YELLOW    = "#f59e0b"   # warning
C_PURPLE    = "#a78bfa"   # koridor 2A
C_TEAL      = "#2dd4bf"   # koridor 2B

WARNA_KORIDOR = {"1": "#22c55e", "2A": "#a78bfa", "2B": "#2dd4bf"}

FONT_TITLE  = QFont("Segoe UI", 15, QFont.Bold)
FONT_BOLD   = QFont("Segoe UI", 12, QFont.Bold)
FONT_REG    = QFont("Segoe UI", 12)
FONT_SMALL  = QFont("Segoe UI", 10)
FONT_MONO   = QFont("Consolas",  11)


# ─────────────────────────────────────────────
# OSRM
# ─────────────────────────────────────────────

def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Jarak dua titik koordinat dalam kilometer."""
    R  = 6371
    d1 = math.radians(lat2 - lat1)
    d2 = math.radians(lon2 - lon1)
    a  = math.sin(d1/2)**2 + math.cos(math.radians(lat1)) * \
         math.cos(math.radians(lat2)) * math.sin(d2/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def get_osrm_route(coords: list[tuple]) -> list[list] | None:
    """Ambil geometri jalan nyata dari OSRM. Fallback None jika gagal."""
    if len(coords) < 2:
        return None
    waypoints = ";".join(f"{lon},{lat}" for lat, lon in coords)
    try:
        r = requests.get(
            f"{OSRM_URL}/{waypoints}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok":
            return [[lat, lon] for lon, lat in
                    data["routes"][0]["geometry"]["coordinates"]]
    except Exception as e:
        print(f"  ⚠️ OSRM error: {e}")
    return None


# ─────────────────────────────────────────────
# Folium map builder
# ─────────────────────────────────────────────

def _circle(m, lat, lon, color, fill, radius, tooltip, popup_html):
    folium.CircleMarker(
        location   = [lat, lon],
        radius     = radius,
        color      = color,
        fill       = True,
        fill_color = fill,
        fill_opacity = 0.92,
        weight     = 2,
        tooltip    = tooltip,
        popup      = folium.Popup(popup_html, max_width=260),
    ).add_to(m)


def build_folium_map(result: RuteResult, halte_list: list) -> str:
    id_ke_halte = {h["id"]: h for h in halte_list}

    m = folium.Map(
        location   = BALIKPAPAN_CENTER,
        zoom_start = 13,
        tiles      = "CartoDB dark_matter",   # tema gelap agar jalur kontras
    )

    # ── Semua halte (background abu kecil) ───────────────────
    for h in halte_list:
        if h.get("lat") and h.get("lon"):
            kor_warna = WARNA_KORIDOR.get(h["koridor"], "#64748b")
            _circle(m, h["lat"], h["lon"],
                    "#334155", "#475569", 3,
                    f"🚏 {h['nama']} [Kor.{h['koridor']}]",
                    f"<b>{h['nama']}</b><br>Koridor {h['koridor']}<br>ID: {h['id']}")

    if not result.ditemukan or not result.rute_id:
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                          mode="w", encoding="utf-8")
        m.save(tmp.name)
        return tmp.name

    # ── Koordinat rute (hanya yang punya lat/lon) ─────────────
    coords_rute = []
    for hid in result.rute_id:
        h = id_ke_halte.get(hid, {})
        if h.get("lat") and h.get("lon"):
            coords_rute.append((h["lat"], h["lon"]))

    # ── Hitung jarak total (km) ───────────────────────────────
    total_km = 0.0
    for i in range(len(coords_rute) - 1):
        total_km += _haversine(*coords_rute[i], *coords_rute[i+1])

    # ── Gambar jalur ──────────────────────────────────────────
    if len(coords_rute) >= 2:
        line = get_osrm_route(coords_rute) or coords_rute

        # Shadow hitam agar kontras di peta gelap
        folium.PolyLine(line, color="#000000", weight=10,
                        opacity=0.35).add_to(m)
        # Jalur utama hijau terang
        folium.PolyLine(
            line, color="#00e676", weight=5, opacity=0.95,
            tooltip=f"🚌 {result.nama_asal} → {result.nama_tujuan} | "
                    f"~{total_km:.1f} km | {result.total_waktu} menit"
        ).add_to(m)

    # ── Gambar node rute ──────────────────────────────────────
    transit_ids = {t.di_halte_id for t in result.transit}

    for i, hid in enumerate(result.rute_id):
        h = id_ke_halte.get(hid, {})
        if not (h.get("lat") and h.get("lon")):
            continue   # skip halte tanpa koordinat (tidak muncul di peta)

        lat  = h["lat"]
        lon  = h["lon"]
        nama = h.get("nama", hid)
        kor  = h.get("koridor", "")
        no   = i + 1

        if hid == result.rute_id[0]:
            # ASAL → ikon marker hijau
            folium.Marker(
                [lat, lon],
                tooltip = f"🟢 ASAL ({no}): {nama}",
                popup   = folium.Popup(
                    f"<b style='color:#22c55e'>🟢 ASAL</b><br>"
                    f"<b>{nama}</b><br>Koridor {kor}<br>Halte ke-{no}",
                    max_width=260),
                icon = folium.Icon(color="green", icon="home", prefix="fa"),
            ).add_to(m)

        elif hid == result.rute_id[-1]:
            # TUJUAN → ikon marker merah
            folium.Marker(
                [lat, lon],
                tooltip = f"🔴 TUJUAN ({no}): {nama}",
                popup   = folium.Popup(
                    f"<b style='color:#ef4444'>🔴 TUJUAN</b><br>"
                    f"<b>{nama}</b><br>Koridor {kor}<br>Halte ke-{no}",
                    max_width=260),
                icon = folium.Icon(color="red", icon="flag", prefix="fa"),
            ).add_to(m)

        elif hid in transit_ids:
            # TRANSIT → lingkaran biru lebih besar
            t    = next((t for t in result.transit if t.di_halte_id == hid), None)
            info = f"Kor.{t.dari_koridor} → Kor.{t.ke_koridor}" if t else ""
            _circle(m, lat, lon,
                    "#1d4ed8", "#3b82f6", 11,
                    f"🔵 TRANSIT ({no}): {nama}",
                    f"<b style='color:#60a5fa'>🔵 TRANSIT</b><br>"
                    f"<b>{nama}</b><br>{info}<br>Halte ke-{no}")

        else:
            # Halte dilewati biasa
            _circle(m, lat, lon,
                    "#475569", "#94a3b8", 7,
                    f"● {no}. {nama}",
                    f"<b>{no}. {nama}</b><br>Koridor {kor}")

    # ── Fit bounds ────────────────────────────────────────────
    if len(coords_rute) >= 2:
        lats = [c[0] for c in coords_rute]
        lons = [c[1] for c in coords_rute]
        m.fit_bounds([
            [min(lats) - 0.01, min(lons) - 0.01],
            [max(lats) + 0.01, max(lons) + 0.01],
        ])

    # ── Simpan info jarak ke result (sementara via attribute) ─
    result._total_km = round(total_km, 2)

    # ── Legend ────────────────────────────────────────────────
    m.get_root().html.add_child(folium.Element(f"""
    <div style="
        position:fixed; bottom:20px; right:20px; z-index:1000;
        background:rgba(15,25,35,0.92);
        border:1px solid #243447;
        border-radius:10px;
        padding:12px 16px;
        font-family:'Segoe UI',sans-serif;
        font-size:12px; color:#e2e8f0;
        line-height:1.9;
        box-shadow:0 4px 12px rgba(0,0,0,0.5);">
      <div style="font-weight:700;font-size:13px;margin-bottom:4px;">🗺 Keterangan</div>
      <div><span style="color:#00e676;font-weight:bold;">━━━</span> Jalur Rute</div>
      <div><span style="color:#22c55e;">⬤</span> Halte Asal</div>
      <div><span style="color:#ef4444;">⬤</span> Halte Tujuan</div>
      <div><span style="color:#3b82f6;">⬤</span> Titik Transit</div>
      <div><span style="color:#94a3b8;">⬤</span> Halte Dilewati</div>
      <div><span style="color:#475569;">⬤</span> Halte Lainnya</div>
      <div style="margin-top:6px;border-top:1px solid #243447;padding-top:6px;color:#64748b;font-size:11px;">
        Klik halte untuk info detail
      </div>
    </div>"""))

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                      mode="w", encoding="utf-8")
    m.save(tmp.name)
    return tmp.name, getattr(result, "_total_km", 0.0)


# ─────────────────────────────────────────────
# Worker thread
# ─────────────────────────────────────────────

class RouteWorker(QThread):
    selesai = pyqtSignal(object, str, float)   # result, html_path, km

    def __init__(self, graph, halte_list, id_asal, id_tujuan, pelajar):
        super().__init__()
        self.graph      = graph
        self.halte_list = halte_list
        self.id_asal    = id_asal
        self.id_tujuan  = id_tujuan
        self.pelajar    = pelajar

    def run(self):
        result            = cari_rute(self.graph, self.halte_list,
                                      self.id_asal, self.id_tujuan, self.pelajar)
        html_path, km_val = build_folium_map(result, self.halte_list)
        self.selesai.emit(result, html_path, km_val)


# ─────────────────────────────────────────────
# Widget Card
# ─────────────────────────────────────────────

class InfoCard(QFrame):
    """
    Card info dengan judul dan grid label:nilai.
    Setiap card punya garis kiri berwarna (accent bar).
    """

    def __init__(self, judul: str, warna_aksen: str = C_ACCENT, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background  : {C_CARD};
                border-left : 4px solid {warna_aksen};
                border-radius: 8px;
                margin-bottom: 6px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(6)

        # Header judul
        lbl = QLabel(judul)
        lbl.setFont(FONT_BOLD)
        lbl.setStyleSheet(f"color:{warna_aksen}; background:transparent;")
        outer.addWidget(lbl)

        # Grid untuk baris isi
        self._grid = QGridLayout()
        self._grid.setSpacing(3)
        self._grid.setColumnStretch(1, 1)
        outer.addLayout(self._grid)
        self._row = 0

    def baris(self, label: str, nilai: str, warna_nilai: str = C_TEXT):
        """Tambah satu baris label : nilai."""
        lk = QLabel(label)
        lk.setFont(FONT_SMALL)
        lk.setStyleSheet(f"color:{C_MUTED}; background:transparent;")
        lk.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lk.setFixedWidth(110)

        lv = QLabel(nilai)
        lv.setFont(FONT_REG)
        lv.setStyleSheet(f"color:{warna_nilai}; background:transparent;")
        lv.setWordWrap(True)
        lv.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self._grid.addWidget(lk, self._row, 0, Qt.AlignTop)
        self._grid.addWidget(lv, self._row, 1, Qt.AlignTop)
        self._row += 1

    def blok(self, teks: str, font=None, warna: str = C_TEXT):
        """Tambah blok teks bebas (misal daftar halte)."""
        lv = QLabel(teks)
        lv.setFont(font or FONT_MONO)
        lv.setStyleSheet(f"color:{warna}; background:transparent;")
        lv.setWordWrap(True)
        lv.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._grid.addWidget(lv, self._row, 0, 1, 2)
        self._row += 1


# ─────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────

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

    # ────────────────── Setup UI ──────────────────────────────

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

        # Form input
        lv.addWidget(self._lbl("📍  Halte Asal"))
        self.combo_asal = self._combo()
        lv.addWidget(self.combo_asal)

        lv.addWidget(self._lbl("🏁  Halte Tujuan"))
        self.combo_tujuan = self._combo()
        lv.addWidget(self.combo_tujuan)

        # Checkbox tarif pelajar
        self.chk_pelajar = QCheckBox("  Tarif Pelajar  (Rp 2.000 / koridor)")
        self.chk_pelajar.setFont(FONT_REG)
        self.chk_pelajar.setStyleSheet(f"color:{C_MUTED};")
        lv.addWidget(self.chk_pelajar)

        # Tombol cari
        self.btn_cari = QPushButton("🔍   Cari Rute")
        self.btn_cari.setFont(FONT_BOLD)
        self.btn_cari.setFixedHeight(48)
        self.btn_cari.setCursor(Qt.PointingHandCursor)
        self.btn_cari.setStyleSheet(f"""
            QPushButton           {{ background:{C_ACCENT}; color:#fff;
                                     border-radius:8px; border:none; }}
            QPushButton:hover     {{ background:#2563eb; }}
            QPushButton:disabled  {{ background:#1e3a5f; color:{C_MUTED}; }}
        """)
        self.btn_cari.clicked.connect(self._cari_rute)
        lv.addWidget(self.btn_cari)

        lv.addWidget(self._divider())

        # Scroll area hasil
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea            {{ background:{C_PANEL}; border:none; }}
            QScrollBar:vertical    {{ background:{C_PANEL}; width:5px; }}
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

        # Status bar bawah
        self.lbl_status = QLabel("⏳ Memuat data...")
        self.lbl_status.setFont(FONT_SMALL)
        self.lbl_status.setStyleSheet(f"color:{C_MUTED};")
        self.lbl_status.setWordWrap(True)
        lv.addWidget(self.lbl_status)

        splitter.addWidget(left)

        # ── Panel kanan (peta) ────────────────────────────────
        self.map_view = QWebEngineView()
        self.map_view.setStyleSheet(f"background:{C_BG};")
        splitter.addWidget(self.map_view)
        splitter.setSizes([440, 860])

        self._tampilkan_peta_kosong()

    # ── Widget helpers ────────────────────────────────────────

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setFont(FONT_BOLD)
        l.setStyleSheet(f"color:{C_MUTED};")
        return l

    def _combo(self) -> QComboBox:
        c = QComboBox()
        c.setEditable(True)
        c.setFixedHeight(40)
        c.setFont(FONT_REG)
        c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        c.setInsertPolicy(QComboBox.NoInsert)
        c.setStyleSheet(f"""
            QComboBox {{
                background  : {C_CARD};
                color       : {C_TEXT};
                border      : 1px solid {C_BORDER};
                border-radius: 6px;
                padding     : 4px 10px;
            }}
            QComboBox:focus {{ border:1px solid {C_ACCENT}; }}
            QComboBox QAbstractItemView {{
                background  : {C_CARD};
                color       : {C_TEXT};
                selection-background-color: {C_ACCENT};
                border      : 1px solid {C_BORDER};
                font-size   : 12px;
            }}
        """)
        return c

    def _divider(self) -> QFrame:
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
                f"✅  {len(self.halte_list)} halte  |  {n_edge} edge  |  siap digunakan"
            )
        except Exception as e:
            self.lbl_status.setText(f"❌ Error saat load: {e}")

    def _isi_combo(self):
        # Kelompokkan per koridor agar dropdown lebih terstruktur
        items = sorted(
            [(f"[Kor.{h['koridor']}]  {h['nama']}", h["id"])
             for h in self.halte_list],
            key=lambda x: (x[0]),
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

        # Loading card sementara
        c = InfoCard("⏳ Sedang menghitung...", C_YELLOW)
        c.blok("Mohon tunggu, algoritma Dijkstra sedang bekerja.",
               font=FONT_REG, warna=C_MUTED)
        self.hasil_layout.addWidget(c)

        self.worker = RouteWorker(
            self.graph, self.halte_list, id_asal, id_tujuan,
            self.chk_pelajar.isChecked()
        )
        self.worker.selesai.connect(self._tampilkan_hasil)
        self.worker.start()

    # ── Tampilkan hasil ───────────────────────────────────────

    def _tampilkan_hasil(self, result: RuteResult, html_path: str, km: float):
        self.btn_cari.setEnabled(True)
        self.btn_cari.setText("🔍   Cari Rute")
        self._clear_hasil()

        # ── Rute tidak ditemukan ──────────────────────────────
        if not result.ditemukan:
            c = InfoCard("❌  Rute Tidak Ditemukan", C_RED)
            c.blok(result.pesan, font=FONT_REG, warna=C_RED)
            self.hasil_layout.addWidget(c)
            self.lbl_status.setText("Rute tidak ditemukan.")
            self._tampilkan_peta_kosong()
            return

        # ── Card ringkasan ────────────────────────────────────
        c1 = InfoCard("✅  Ringkasan Perjalanan", C_GREEN)
        c1.baris("⏱ Waktu",        f"{result.total_waktu} menit", C_TEXT)
        c1.baris("📏 Jarak",        f"~{km:.1f} km (estimasi)", C_TEXT)
        c1.baris("🚏 Halte dilalui", f"{result.jumlah_halte} halte", C_TEXT)
        c1.baris("🔄 Transit",
                 f"{len(result.transit)}x transit" if result.transit
                 else "Tidak ada transit (1 koridor langsung)", C_TEXT)
        c1.baris("🛤 Koridor",
                 "  →  ".join(
                     f"Kor.{k}" for k in result.koridor_dipakai
                 ) if result.koridor_dipakai else "-", C_TEXT)
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
                    C_BLUE
                )
            self.hasil_layout.addWidget(c2)

        # ── Card urutan halte (dikelompokkan per koridor) ─────
        c3 = InfoCard("📍  Urutan Halte yang Dilewati", C_MUTED)

        transit_ids = {t.di_halte_id for t in result.transit}

        # Susun teks per segmen koridor
        teks       = ""
        kor_aktif  = None

        # Ambil info koridor per halte dari path (bukan result.rute_id saja)
        # Kita bisa infer dari koridor_dipakai dan transit
        halte_info = {h["id"]: h for h in self.halte_list}

        for i, (hid, nama) in enumerate(zip(result.rute_id, result.rute_nama)):
            h   = halte_info.get(hid, {})
            kor = h.get("koridor", "?")

            # Header koridor ketika berganti
            if kor != kor_aktif:
                if kor_aktif is not None:
                    teks += "\n"
                warna_kor = {"1": "🟩", "2A": "🟪", "2B": "🟦"}.get(kor, "⬜")
                teks += f"{warna_kor} ─── Koridor {kor} ───\n"
                kor_aktif = kor

            if   hid == result.rute_id[0]:   ikon = "🟢"
            elif hid == result.rute_id[-1]:  ikon = "🔴"
            elif hid in transit_ids:         ikon = "🔵"
            else:                            ikon = "  ○"

            teks += f"  {ikon} {i+1:02d}. {nama}\n"

        c3.blok(teks.strip())
        self.hasil_layout.addWidget(c3)

        # ── Load peta ─────────────────────────────────────────
        if self._tmp_html:
            try:
                os.unlink(self._tmp_html)
            except Exception:
                pass
        self._tmp_html = html_path
        self.map_view.load(QUrl.fromLocalFile(html_path))

        self.lbl_status.setText(
            f"✅ {result.nama_asal} → {result.nama_tujuan}  |  "
            f"{result.total_waktu} mnt  |  ~{km:.1f} km  |  "
            f"Rp {result.total_biaya:,}"
        )

    # ── Peta kosong ───────────────────────────────────────────

    def _tampilkan_peta_kosong(self):
        m = folium.Map(
            location   = BALIKPAPAN_CENTER,
            zoom_start = 13,
            tiles      = "CartoDB dark_matter",
        )

        # Tampilkan semua halte sebagai titik abu
        for h in self.halte_list:
            if h.get("lat") and h.get("lon"):
                kor_warna = WARNA_KORIDOR.get(h["koridor"], "#64748b")
                _circle(m, h["lat"], h["lon"],
                        "#334155", kor_warna, 4,
                        f"🚏 {h['nama']} [Kor.{h['koridor']}]",
                        f"<b>{h['nama']}</b><br>Koridor {h['koridor']}")

        # Legend sederhana
        m.get_root().html.add_child(folium.Element("""
        <div style="
            position:fixed; bottom:20px; right:20px; z-index:1000;
            background:rgba(15,25,35,0.92);
            border:1px solid #243447; border-radius:10px;
            padding:12px 16px;
            font-family:'Segoe UI',sans-serif;
            font-size:12px; color:#e2e8f0; line-height:1.9;
            box-shadow:0 4px 12px rgba(0,0,0,0.5);">
          <div style="font-weight:700;font-size:13px;margin-bottom:4px;">🗺 Semua Halte Bacitra</div>
          <div><span style="color:#22c55e;">⬤</span> Koridor 1</div>
          <div><span style="color:#a78bfa;">⬤</span> Koridor 2A</div>
          <div><span style="color:#2dd4bf;">⬤</span> Koridor 2B</div>
        </div>"""))

        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                          mode="w", encoding="utf-8")
        m.save(tmp.name)
        self.map_view.load(QUrl.fromLocalFile(tmp.name))


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
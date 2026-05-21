"""
data/halte_raw.py
─────────────────
Data halte Balikpapan City Trans (Bacitra)
Sumber: Transit Network Map of Balikpapan (CC BY 4.0)
        Desain: Farhan S. Fadhillah & Fajar Muhammad — 2026-05-01

Penamaan koridor resmi:
1   → Pelabuhan Semayang - Bandara Sepinggan (PP)
2A  → Terminal Batu Ampar - Plaza Balikpapan via MT. Haryono
2B  → Terminal Batu Ampar - Plaza Balikpapan via Rapak (Ahmad Yani)
D   → Trans Balikpapan SAUM: Terminal Batu Ampar - Pelabuhan Ferry Kariangau
        (Operasional terbatas, tidak dimasukkan karena beda operator)

Format tiap entry: ("Nama Halte", ["query_utama", "fallback1", ...])
"""

# ── Koridor 1 ──────────────────────────────────────────────────────────────
# Pelabuhan Semayang → Bandara Sepinggan (PP)
# Catatan: rute melingkar, lewat pusat kota bagian bawah peta
# Waktu tempuh total ±95 menit (9 bus, ritase 05:30-21:30)

HALTE_KORIDOR_1 = [
    ("Pelabuhan Semayang",       ["Pelabuhan Semayang Balikpapan"]),
    ("Melawai",                  ["Pantai Melawai Balikpapan", "Jalan Melawai Balikpapan"]),
    ("Lapangan Merdeka",         ["Lapangan Merdeka Balikpapan"]),
    ("RS Pertamina",             ["RS Pertamina Balikpapan", "Rumah Sakit Pertamina Balikpapan"]),
    ("PNW",                      ["Pertamina Hulu Mahakam Balikpapan", "Jalan Sudirman Balikpapan"]),
    ("Banua Patra",              ["Banua Patra Balikpapan", "Jalan Yos Sudarso Balikpapan"]),
    ("Bank Indonesia",           ["Bank Indonesia Balikpapan"]),
    ("SD Bhayangkari",           ["SD Bhayangkari Balikpapan"]),
    ("Kantor Pos",               ["Kantor Pos Balikpapan Kota"]),
    ("Pasar Klandasan",          ["Pasar Klandasan Balikpapan"]),
    ("Terminal Rasa",            ["Terminal Rasa Balikpapan", "Jalan Ahmad Yani Balikpapan"]),
    ("Blauran",                  ["Blauran Balikpapan", "Jalan Blauran Balikpapan"]),
    ("Gedung Parkir Klandasan",  ["Gedung Parkir Klandasan Balikpapan"]),
    ("Simpang Plaza Balikpapan B", ["Plaza Balikpapan", "Mall Plaza Balikpapan"]),
    ("Simpang Plaza Balikpapan A", ["Simpang Plaza Balikpapan", "Plaza Balikpapan Mall"]),  # Titik transit 2A & 2B
    ("BCA",                      ["Bank BCA Balikpapan Kota", "BCA Ahmad Yani Balikpapan"]),
    ("Bank Danamon",             ["Bank Danamon Balikpapan"]),
    ("Bulog",                    ["Bulog Balikpapan", "Perum Bulog Balikpapan"]),
    ("Nuansa",                   ["Nuansa Balikpapan", "Jalan MT Haryono Balikpapan"]),
    ("Balikpapan Permai",        ["Perumahan Balikpapan Permai"]),                           # Titik transit 2A
    ("Ace Hardware",             ["Ace Hardware Balikpapan"]),
    ("Samsat Markoni",           ["Samsat Balikpapan Markoni", "Jalan Markoni Balikpapan"]),
    ("DKK",                      ["Dinas Kesehatan Kota Balikpapan"]),
    ("Pasar Baru",               ["Pasar Baru Balikpapan"]),
    ("Kehutanan",                ["Dinas Kehutanan Balikpapan"]),
    ("Benakatai",                ["Benakatai Balikpapan"]),
    ("Al Ihsan",                 ["Masjid Al Ihsan Balikpapan"]),
    ("SDN 006",                  ["SD Negeri 006 Balikpapan"]),
    ("Mekar Sari",               ["Mekar Sari Balikpapan", "Jalan Mekar Sari Balikpapan"]),
    ("Gunung Pasir",             ["Gunung Pasir Balikpapan", "Kelurahan Gunung Pasir Balikpapan"]),
    ("KPP Pratama Penajam",      ["KPP Pratama Balikpapan", "Kantor Pajak Balikpapan"]),
    ("Puskib",                   ["Puskesmas Klandasan Balikpapan"]),
    ("Pomal",                    ["Pomal Balikpapan", "Polisi Militer Angkatan Laut Balikpapan"]),
    ("SDN 001",                  ["SD Negeri 001 Balikpapan"]),
    ("Karang Jati",              ["Karang Jati Balikpapan"]),
    ("Muara Rapak",              ["Muara Rapak Balikpapan"]),
    ("Ibnu Sina",                ["RS Ibnu Sina Balikpapan", "Rumah Sakit Ibnu Sina Balikpapan"]),
    ("Plaza Rapak",              ["Plaza Rapak Balikpapan"]),
    ("Strat",                    ["Strat Balikpapan", "Jalan Muara Rapak Balikpapan"]),
    ("SMAN 2 Balikpapan",        ["SMA Negeri 2 Balikpapan", "SMAN 2 Balikpapan"]),
    ("Samsat Muara Rapak",       ["Samsat Muara Rapak Balikpapan"]),
    ("SMPN 3 Balikpapan",        ["SMP Negeri 3 Balikpapan"]),
    ("Bengrah",                  ["Bengrah Balikpapan"]),
    ("Inpres 4",                 ["SD Inpres 4 Balikpapan"]),
    ("SMK Setia Budi",           ["SMK Setia Budi Balikpapan"]),
    ("Pulau Indah",              ["Pulau Indah Balikpapan"]),
    ("Simpang Perumnas",         ["Simpang Perumnas Balikpapan"]),
    ("SD Kartika V-3",           ["SD Kartika Balikpapan"]),
    ("Yon Zipur",                ["Batalyon Zeni Tempur Balikpapan"]),
    ("Perintis",                 ["Jalan Perintis Balikpapan"]),
    ("Perumahan Ramayana",       ["Perumahan Ramayana Balikpapan"]),
    ("Pemotongan Hewan",         ["Pemotongan Hewan Balikpapan", "RPH Balikpapan"]),
    ("Graha Indah",              ["Graha Indah Balikpapan"]),
    ("Masjid Santalia",          ["Masjid Santalia Balikpapan"]),
    ("Perum PGRI",               ["Perumahan PGRI Balikpapan"]),
    ("PT. PAC",                  ["PT PAC Balikpapan"]),
    ("Perum Griya Kariangau",    ["Perumahan Griya Kariangau Balikpapan"]),
    ("Puskesmas Kariangau",      ["Puskesmas Kariangau Balikpapan"]),
    ("SMP 16",                   ["SMP 16 Balikpapan", "SMP Negeri 16 Balikpapan"]),
    ("SD 020",                   ["SD 020 Balikpapan"]),
    ("PT Petrosea",              ["PT Petrosea Balikpapan"]),
    ("Kelurahan Kariangau",      ["Kelurahan Kariangau Balikpapan"]),
    ("Pelabuhan Kariangau",      ["Pelabuhan Ferry Kariangau Balikpapan", "Pelabuhan Kariangau Balikpapan"]),
    ("Bandara Sepinggan",        ["Bandara Sepinggan Balikpapan", "Sultan Aji Muhammad Sulaiman Airport"]),
]

# ── Koridor 2A ─────────────────────────────────────────────────────────────
# Terminal Batu Ampar → Plaza Balikpapan via MT. Haryono (PP)
# Waktu tempuh total ±70 menit (6 bus, ritase 05:30-21:30)

HALTE_KORIDOR_2A = [
    ("Terminal Batu Ampar",      ["Terminal Batu Ampar Balikpapan"]),
    ("Sabulussalam",             ["Masjid Sabilussalam Balikpapan", "Jalan Soekarno Hatta Balikpapan"]),
    ("Simpang Batu Ampar",       ["Simpang Batu Ampar Balikpapan"]),
    ("Pasar Butun",              ["Pasar Butun Balikpapan"]),
    ("Al Auliya",                ["Masjid Al Auliya Balikpapan"]),
    ("Pelangi Metro",            ["Pelangi Metro Balikpapan", "Jalan MT Haryono Balikpapan"]),
    ("RSKD",                     ["Rumah Sakit Kanker Dharmais Balikpapan"]),
    ("Grand City",               ["Grand City Mall Balikpapan"]),
    ("Hotel Her",                ["Hotel Her Balikpapan", "Jalan MT Haryono Balikpapan"]),
    ("Global Sport",             ["Global Sport Balikpapan"]),
    ("Daun Village",             ["Daun Village Balikpapan"]),
    ("RS Balikpapan Baru",       ["RS Balikpapan Baru", "Rumah Sakit Balikpapan Baru"]),
    ("Living Plaza",             ["Living Plaza Balikpapan"]),
    ("Majesty",                  ["Majesty Balikpapan"]),
    ("PLN MT Haryono",           ["PLN Balikpapan MT Haryono", "Kantor PLN Balikpapan"]),
    ("Masjid Shahibussalam",     ["Masjid Shahibussalam Balikpapan"]),
    ("RS Siloam",                ["RS Siloam Balikpapan", "Rumah Sakit Siloam Balikpapan"]),
    ("Bukit Damai Indah",        ["Bukit Damai Indah Balikpapan"]),
    ("Kelurahan Damai Baru",     ["Kelurahan Damai Baru Balikpapan"]),
    ("Dukcapil",                 ["Dinas Kependudukan Balikpapan", "Disdukcapil Balikpapan"]),
    ("Beller",                   ["Jalan Beller Balikpapan"]),
    ("B-Connect",                ["B Connect Balikpapan"]),
    ("Kolam Mulawarman",         ["Kolam Renang Mulawarman Balikpapan"]),
    ("SDN 012",                  ["SD Negeri 012 Balikpapan"]),
    ("Mekar Sari",               ["Mekar Sari Balikpapan"]),                                # Titik transit dgn Kor 1
    ("Kavling 8 Square",         ["Kavling 8 Square Balikpapan", "Ruko Kavling 8 Balikpapan"]),
    ("Siaga",                    ["Siaga Balikpapan"]),
    ("Balikpapan Permai",        ["Perumahan Balikpapan Permai"]),                           # Titik transit dgn Kor 1
    ("Ace Hardware",             ["Ace Hardware Balikpapan"]),
    ("Samsat Markoni",           ["Samsat Balikpapan Markoni", "Jalan Markoni Balikpapan"]), # Titik transit dgn Kor 1
    ("DKK",                      ["Dinas Kesehatan Kota Balikpapan"]),
    ("Pasar Baru",               ["Pasar Baru Balikpapan"]),
    ("Simpang Plaza Balikpapan A", ["Simpang Plaza Balikpapan", "Plaza Balikpapan Mall"]),  # TERMINAL / PUTAR BALIK
]

# ── Koridor 2B ─────────────────────────────────────────────────────────────
# Terminal Batu Ampar → Plaza Balikpapan via Rapak / Ahmad Yani (PP)
# Waktu tempuh total ±70 menit (6 bus, ritase 05:35-21:35)

HALTE_KORIDOR_2B = [
    ("Terminal Batu Ampar",      ["Terminal Batu Ampar Balikpapan"]),
    ("Pegadaian",                ["Pegadaian Balikpapan", "Kantor Pegadaian Balikpapan"]),
    ("Samsat Muara Rapak",       ["Samsat Muara Rapak Balikpapan"]),
    ("Plaza Rapak",              ["Plaza Rapak Balikpapan"]),
    ("Ibnu Sina",                ["RS Ibnu Sina Balikpapan", "Rumah Sakit Ibnu Sina Balikpapan"]),
    ("SMAN 2 Balikpapan",        ["SMA Negeri 2 Balikpapan"]),
    ("Strat",                    ["Strat Balikpapan", "Jalan Muara Rapak Balikpapan"]),
    ("Muara Rapak",              ["Muara Rapak Balikpapan"]),
    ("Karang Jati",              ["Karang Jati Balikpapan"]),
    ("SDN 001",                  ["SD Negeri 001 Balikpapan"]),
    ("Pomal",                    ["Pomal Balikpapan"]),
    ("Puskib",                   ["Puskesmas Klandasan Balikpapan"]),
    ("KPP Pratama Penajam",      ["KPP Pratama Balikpapan", "Kantor Pajak Balikpapan"]),
    ("Gunung Pasir",             ["Gunung Pasir Balikpapan"]),
    ("SDN 006",                  ["SD Negeri 006 Balikpapan"]),
    ("Al Ihsan",                 ["Masjid Al Ihsan Balikpapan"]),
    ("Mekar Sari",               ["Mekar Sari Balikpapan"]),
    ("Kehutanan",                ["Dinas Kehutanan Balikpapan"]),
    ("Benakatai",                ["Benakatai Balikpapan"]),
    ("Simpang Plaza Balikpapan A", ["Simpang Plaza Balikpapan", "Plaza Balikpapan Mall"]),  # TERMINAL / PUTAR BALIK
]

# ── Konfigurasi bobot waktu ────────────────────────────────────────────────
# Estimasi dari jadwal @temanbusbalikpapan (update 9 Feb 2026)

BOBOT_KORIDOR = {
    "1":  4,   # ±95 menit / ~60 halte (lewat Kariangau)
    "2A": 2,   # ±70 menit / ~33 halte
    "2B": 4,   # ±70 menit / ~20 halte
}

WAKTU_TRANSIT = 10  # menit, estimasi waktu pindah bus di halte transit
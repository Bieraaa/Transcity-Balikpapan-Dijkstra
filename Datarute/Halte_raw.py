"""
Koridor:
1  → Pelabuhan Semayang - Bandara Sepinggan (PP)
2A → Terminal Batu Ampar - Plaza Balikpapan via MT. Haryono
2B → Terminal Batu Ampar - Plaza Balikpapan via Rapak (Ahmad Yani)
D  → Trans Balikpapan SAUM (beda operator, tidak dimasukkan)
"""
# ── Koridor 1 ──────────────────────────────────────────────────────────────
# Rute: Pelabuhan Semayang → pusat kota → Bandara → Kariangau (melingkar)
# Waktu tempuh: ±95 menit | 9 bus | Ritase 05:30 - 21:30

HALTE_KORIDOR_1 = [
    # ── Segmen: Pesisir → Pusat Kota ──
    ("Pelabuhan Semayang",          ["Pelabuhan Semayang Balikpapan"]),
    ("Melawai",                     ["Pantai Melawai Balikpapan", "Jalan Melawai Balikpapan"]),
    ("Lapangan Merdeka",            ["Lapangan Merdeka Balikpapan"]),
    ("RS Pertamina",                ["RS Pertamina Balikpapan"]),
    ("PNW",                         ["Pertamina Hulu Mahakam Balikpapan", "Jalan Sudirman Balikpapan"]),
    ("Banua Patra",                 ["Banua Patra Balikpapan"]),
    ("Bank Indonesia",              ["Bank Indonesia Balikpapan"]),
    ("SD Bhayangkari",              ["SD Bhayangkari Balikpapan"]),
    ("Kantor Pos",                  ["Kantor Pos Balikpapan Kota"]),
    ("Pasar Klandasan",             ["Pasar Klandasan Balikpapan"]),
    ("Terminal Rasa",               ["Terminal Rasa Balikpapan"]),
    ("Blauran",                     ["Blauran Balikpapan"]),
    ("Gedung Parkir Klandasan",     ["Gedung Parkir Klandasan Balikpapan"]),
    ("Simpang Plaza Balikpapan B",  ["Plaza Balikpapan Mall", "Mall Plaza Balikpapan"]),
    ("Simpang Plaza Balikpapan A",  ["Simpang Plaza Balikpapan"]),               # ← TRANSIT 2A & 2B

    # ── Segmen: Pusat Kota → Timur (MT Haryono) ──
    ("BCA",                         ["Bank BCA Balikpapan Kota"]),
    ("Bank Danamon",                ["Bank Danamon Balikpapan"]),
    ("Bulog",                       ["Bulog Balikpapan"]),
    ("Nuansa",                      ["Nuansa Balikpapan", "Jalan MT Haryono Balikpapan"]),
    ("Balikpapan Permai",           ["Perumahan Balikpapan Permai"]),             # ← TRANSIT 2A
    ("Balikpapan Superblock",       ["Balikpapan Superblock BSB", "BSB City Balikpapan"]),
    ("Rutan Balikpapan",            ["Rutan Balikpapan", "Rumah Tahanan Balikpapan"]),
    ("Trakindo",                    ["Trakindo Balikpapan"]),
    ("Asabri",                      ["Asabri Balikpapan"]),
    ("Disporapar",                  ["Disporapar Balikpapan", "Dinas Pemuda Olahraga Balikpapan"]),
    ("Taman Makam Pahlawan",        ["Taman Makam Pahlawan Balikpapan"]),
    ("SMPN 10",                     ["SMP Negeri 10 Balikpapan"]),
    ("Masjid Al Aqsha",             ["Masjid Al Aqsha Balikpapan"]),
    ("Gang Mawar",                  ["Gang Mawar Balikpapan"]),
    ("BPJS Kaltim",                 ["BPJS Kesehatan Balikpapan"]),
    ("Grand Tjokro",                ["Grand Tjokro Balikpapan", "Hotel Grand Tjokro Balikpapan"]),
    ("SDN 007 Balikpapan Selatan",  ["SD Negeri 007 Balikpapan Selatan"]),
    ("Bandara Luar",                ["Bandara Sepinggan Luar Balikpapan"]),

    # ── Titik Ujung Timur ──
    ("Bandara Sepinggan",           ["Bandara Sepinggan Balikpapan", "Sultan Aji Muhammad Sulaiman Airport"]),

    # ── Segmen: Balik ke Barat via Jl. Markoni ──
    ("Ace Hardware",                ["Ace Hardware Balikpapan"]),
    ("Samsat Markoni",              ["Samsat Balikpapan Markoni"]),
    ("DKK",                         ["Dinas Kesehatan Kota Balikpapan"]),
    ("Pasar Baru",                  ["Pasar Baru Balikpapan"]),
    ("Kehutanan",                   ["Dinas Kehutanan Balikpapan"]),
    ("Benakutai",                   ["Benakutai Balikpapan"]),
    ("Restu Ibu",                   ["Restu Ibu Balikpapan"]),
    ("Al Ihsan",                    ["Masjid Al Ihsan Balikpapan"]),
    ("SDN 006",                     ["SD Negeri 006 Balikpapan"]),
    ("Mekar Sari",                  ["Mekar Sari Balikpapan"]),                  # ← TRANSIT 2A & 2B
    ("Gunung Pasir",                ["Gunung Pasir Balikpapan"]),
    ("KPP Pratama Penajam",         ["KPP Pratama Balikpapan"]),
    ("Puskib",                      ["Puskesmas Klandasan Balikpapan"]),
    ("Pomal",                       ["Pomal Balikpapan"]),
    ("SDN 001",                     ["SD Negeri 001 Balikpapan"]),
    ("Karang Jati",                 ["Karang Jati Balikpapan"]),
    ("Muara Rapak",                 ["Muara Rapak Balikpapan"]),
    ("Ibnu Sina",                   ["RS Ibnu Sina Balikpapan"]),
    ("Plaza Rapak",                 ["Plaza Rapak Balikpapan"]),
    ("Strat",                       ["Strat Balikpapan", "Jalan Muara Rapak Balikpapan"]),
    ("SMAN 2 Balikpapan",           ["SMA Negeri 2 Balikpapan"]),
    ("Samsat Muara Rapak",          ["Samsat Muara Rapak Balikpapan"]),
    ("SMPN 3 Balikpapan",           ["SMP Negeri 3 Balikpapan"]),
    ("Bengrah",                     ["Bengrah Balikpapan"]),
    ("Inpres 4",                    ["SD Inpres 4 Balikpapan"]),
    ("SMK Setia Budi",              ["SMK Setia Budi Balikpapan"]),
    ("Pulau Indah",                 ["Pulau Indah Balikpapan"]),
    ("Simpang Perumnas",            ["Simpang Perumnas Balikpapan"]),
    ("SD Kartika V-3",              ["SD Kartika Balikpapan"]),
    ("Yon Zipur",                   ["Batalyon Zeni Tempur Balikpapan"]),
    ("Perintis",                    ["Jalan Perintis Balikpapan"]),
    ("Perumahan Ramayana",          ["Perumahan Ramayana Balikpapan"]),

    # ── Segmen: Menuju Kariangau ──
    ("Pemotongan Hewan",            ["Pemotongan Hewan Balikpapan", "RPH Balikpapan"]),
    ("Graha Indah",                 ["Graha Indah Balikpapan"]),
    ("Masjid Santalia",             ["Masjid Santalia Balikpapan"]),
    ("Perum PGRI",                  ["Perumahan PGRI Balikpapan"]),
    ("PT. PAC",                     ["PT PAC Balikpapan"]),
    ("Perum Griya Kariangau",       ["Perumahan Griya Kariangau Balikpapan"]),
    ("Puskesmas Kariangau",         ["Puskesmas Kariangau Balikpapan"]),
    ("SMP 16",                      ["SMP Negeri 16 Balikpapan"]),
    ("SD 020",                      ["SD 020 Balikpapan"]),
    ("PT Petrosea",                 ["PT Petrosea Balikpapan"]),
    ("Kelurahan Kariangau",         ["Kelurahan Kariangau Balikpapan"]),
    ("Pelabuhan Kariangau",         ["Pelabuhan Ferry Kariangau Balikpapan"]),
]

# ── Koridor 2A ─────────────────────────────────────────────────────────────
# Rute: Terminal Batu Ampar → Jl. MT Haryono → Plaza Balikpapan (PP)
# Waktu tempuh: ±70 menit | 6 bus | Ritase 05:30 - 21:30

HALTE_KORIDOR_2A = [
    ("Terminal Batu Ampar",         ["Terminal Batu Ampar Balikpapan"]),          # ← TRANSIT 2B
    ("Sabulussalam",                ["Masjid Sabilussalam Balikpapan"]),
    ("Simpang Batu Ampar",          ["Simpang Batu Ampar Balikpapan"]),
    ("Pasar Butun",                 ["Pasar Butun Balikpapan"]),
    ("Al Auliya",                   ["Masjid Al Auliya Balikpapan"]),
    ("Pelangi Metro",               ["Pelangi Metro Balikpapan"]),
    ("RSKD",                        ["Rumah Sakit Kanker Dharmais Balikpapan"]),
    ("Grand City",                  ["Grand City Mall Balikpapan"]),
    ("Hotel Her",                   ["Hotel Her Balikpapan"]),
    ("Global Sport",                ["Global Sport Balikpapan"]),
    ("Daun Village",                ["Daun Village Balikpapan"]),
    ("RS Balikpapan Baru",          ["RS Balikpapan Baru"]),
    ("Living Plaza",                ["Living Plaza Balikpapan"]),
    ("Majesty",                     ["Majesty Balikpapan"]),
    ("PLN MT Haryono",              ["PLN Balikpapan MT Haryono"]),
    ("Masjid Shahibussalam",        ["Masjid Shahibussalam Balikpapan"]),
    ("RS Siloam",                   ["RS Siloam Balikpapan"]),
    ("Bukit Damai Indah",           ["Bukit Damai Indah Balikpapan"]),
    ("Kelurahan Damai Baru",        ["Kelurahan Damai Baru Balikpapan"]),
    ("Dukcapil",                    ["Disdukcapil Balikpapan"]),
    ("Beller",                      ["Jalan Beller Balikpapan"]),
    ("B-Connect",                   ["B Connect Balikpapan"]),
    ("Kolam Mulawarman",            ["Kolam Renang Mulawarman Balikpapan"]),
    ("SDN 012",                     ["SD Negeri 012 Balikpapan"]),
    ("Mekar Sari",                  ["Mekar Sari Balikpapan"]),                  # ← TRANSIT 1 & 2B
    ("Kavling 8 Square",            ["Kavling 8 Square Balikpapan"]),
    ("Siaga",                       ["Siaga Balikpapan"]),
    ("Balikpapan Permai",           ["Perumahan Balikpapan Permai"]),             # ← TRANSIT 1
    ("Ace Hardware",                ["Ace Hardware Balikpapan"]),
    ("Samsat Markoni",              ["Samsat Balikpapan Markoni"]),
    ("DKK",                         ["Dinas Kesehatan Kota Balikpapan"]),
    ("Pasar Baru",                  ["Pasar Baru Balikpapan"]),
    ("Simpang Plaza Balikpapan A",  ["Simpang Plaza Balikpapan"]),               # ← TRANSIT 1 & 2B
]

# ── Koridor 2B ─────────────────────────────────────────────────────────────
# Rute: Terminal Batu Ampar → Jl. Ahmad Yani → Rapak → Plaza Balikpapan (PP)
# Waktu tempuh: ±70 menit | 6 bus | Ritase 05:35 - 21:35

HALTE_KORIDOR_2B = [
    ("Terminal Batu Ampar",         ["Terminal Batu Ampar Balikpapan"]),          # ← TRANSIT 2A
    ("Pegadaian",                   ["Pegadaian Balikpapan"]),
    ("Samsat Muara Rapak",          ["Samsat Muara Rapak Balikpapan"]),
    ("Plaza Rapak",                 ["Plaza Rapak Balikpapan"]),
    ("Ibnu Sina",                   ["RS Ibnu Sina Balikpapan"]),
    ("SMAN 2 Balikpapan",           ["SMA Negeri 2 Balikpapan"]),
    ("Strat",                       ["Strat Balikpapan"]),
    ("Muara Rapak",                 ["Muara Rapak Balikpapan"]),
    ("Karang Jati",                 ["Karang Jati Balikpapan"]),
    ("SDN 001",                     ["SD Negeri 001 Balikpapan"]),
    ("Pomal",                       ["Pomal Balikpapan"]),
    ("Puskib",                      ["Puskesmas Klandasan Balikpapan"]),
    ("KPP Pratama Penajam",         ["KPP Pratama Balikpapan"]),
    ("Gunung Pasir",                ["Gunung Pasir Balikpapan"]),
    ("SDN 006",                     ["SD Negeri 006 Balikpapan"]),
    ("Al Ihsan",                    ["Masjid Al Ihsan Balikpapan"]),
    ("Mekar Sari",                  ["Mekar Sari Balikpapan"]),                  # ← TRANSIT 1 & 2A
    ("Kehutanan",                   ["Dinas Kehutanan Balikpapan"]),
    ("Benakutai",                   ["Benakutai Balikpapan"]),
    ("Simpang Plaza Balikpapan A",  ["Simpang Plaza Balikpapan"]),               # ← TRANSIT 1 & 2A
]

# ── Bobot waktu tempuh antar halte (menit) ─────────────────────────────────
# Estimasi dari jadwal @temanbusbalikpapan (update 9 Feb 2026)
BOBOT_KORIDOR = {
    "1":  2,   # ±95 menit / ~78 halte
    "2A": 2,   # ±70 menit / ~33 halte
    "2B": 4,   # ±70 menit / ~20 halte
}

WAKTU_TRANSIT = 10  # menit — estimasi waktu tunggu + pindah bus
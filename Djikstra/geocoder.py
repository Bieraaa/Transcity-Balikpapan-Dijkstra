import time
import sys
import requests

NOMINATIM_URL   = "https://nominatim.openstreetmap.org/search"
HEADERS         = {"User-Agent": "BacitraRouteApp/1.0 (tugas-kuliah-balikpapan)"}
BALIKPAPAN_BBOX = "116.70,-1.40,117.05,-1.05"   # lon_min, lat_min, lon_max, lat_max
DELAY_DETIK     = 1.1

def _fetch(query : str) -> dict | None :
    params = {
        "q": query,
        "format": "json",
        "limit" : 1,
        "countrycodes": "id",
        "viewbox": BALIKPAPAN_BBOX,
        "bounded": 1
    }
    
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            return {
                "lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])
            }
    except Exception as e:
        print(f"      ⚠️  Request error: {e}", file=sys.stderr)
        return None
    
def cari_koordinat(nama: str, queries: list[str]) -> dict:
    for q in queries:
        print(f"    🔍 '{q}'")
        result = _fetch(q)
        time.sleep(DELAY_DETIK)
        
        if result:
            print(f"    ✅ ({result['lat']:.5f}, {result['lon']:.5f})")
            return{
                "nama": nama,
                "lat": result["lat"],
                "lon": result["lon"],
                "query_berhasil": q,
                "status": "found"
            }

        print(f"    ❌ Tidak ditemukan → perlu input manual")
        return {
        "nama":           nama,
        "lat":            None,
        "lon":            None,
        "query_berhasil": None,
        "status":         "not_found",
        }
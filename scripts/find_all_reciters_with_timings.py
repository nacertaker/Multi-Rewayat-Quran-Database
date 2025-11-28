"""
البحث عن جميع القراء الذين لديهم توقيتات
"""

import requests
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://mp3quran.net/api/v3"

def get_all_reciters():
    """الحصول على جميع القراء"""
    response = requests.get(f"{BASE_URL}/reciters", params={"language": "ar"})
    return response.json().get('reciters', [])

def check_has_timings(reciter_id):
    """التحقق من وجود توقيتات للقارئ"""
    try:
        response = requests.get(f"{BASE_URL}/ayat_timing", params={
            "read": reciter_id,
            "sura": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return True
        return False
    except:
        return False

def main():
    print("=" * 70)
    print("البحث عن جميع القراء الذين لديهم توقيتات")
    print("=" * 70)
    
    # الحصول على القراء
    print("\n1. جاري تحميل قائمة القراء...")
    reciters = get_all_reciters()
    print(f"   عدد القراء: {len(reciters)}")
    
    # فحص كل قارئ
    print("\n2. جاري فحص القراء...")
    
    reciters_with_timings = []
    
    for i, reciter in enumerate(reciters):
        # عرض التقدم
        if (i + 1) % 20 == 0:
            print(f"   تم فحص {i + 1}/{len(reciters)} قارئ...")
        
        has_timings = check_has_timings(reciter['id'])
        
        if has_timings:
            for moshaf in reciter.get('moshaf', []):
                reciters_with_timings.append({
                    'reciter_id': reciter['id'],
                    'reciter_name': reciter['name'],
                    'moshaf_id': moshaf['id'],
                    'moshaf_name': moshaf['name'],
                    'server': moshaf['server'],
                    'surah_total': moshaf.get('surah_total', 0)
                })
        
        # تأخير بسيط
        time.sleep(0.05)
    
    print(f"\n3. النتائج:")
    print(f"   القراء مع توقيتات: {len(reciters_with_timings)}")
    
    # تصنيف حسب الرواية
    riwayat = {
        'حفص': [],
        'ورش': [],
        'قالون': [],
        'الدوري': [],
        'شعبة': [],
        'السوسي': []
    }
    
    for r in reciters_with_timings:
        moshaf_name = r['moshaf_name']
        for riwayah in riwayat.keys():
            if riwayah in moshaf_name:
                riwayat[riwayah].append(r)
                break
    
    print("\n4. تصنيف حسب الرواية:")
    for riwayah, readers in riwayat.items():
        complete = [r for r in readers if r['surah_total'] == 114]
        print(f"\n   {riwayah}:")
        print(f"      إجمالي: {len(readers)}")
        print(f"      كامل (114 سورة): {len(complete)}")
        
        for r in complete:
            print(f"      - {r['reciter_name']} ({r['moshaf_name']})")
    
    # حفظ النتائج
    output_path = Path("data/audio_recitations/reciters_with_timings.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(reciters_with_timings),
            'reciters': reciters_with_timings,
            'by_riwayah': {k: v for k, v in riwayat.items()}
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n5. تم الحفظ في: {output_path}")

if __name__ == "__main__":
    main()



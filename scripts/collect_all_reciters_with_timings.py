"""
جمع بيانات جميع القراء الذين لديهم توقيتات
"""

import requests
import json
import sys
import time
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://mp3quran.net/api/v3"
OUTPUT_DIR = Path("data/audio_recitations")

def get_surah_timings(reciter_id, surah_number):
    """الحصول على توقيتات سورة معينة"""
    try:
        response = requests.get(f"{BASE_URL}/ayat_timing", params={
            "read": reciter_id,
            "sura": surah_number
        })
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data
        return None
    except Exception as e:
        return None

def collect_reciter_data(reciter_info):
    """جمع بيانات قارئ كامل"""
    
    reciter_id = reciter_info['reciter_id']
    reciter_name = reciter_info['reciter_name']
    
    all_data = {
        'reciter_id': reciter_id,
        'reciter_name': reciter_name,
        'moshaf_id': reciter_info['moshaf_id'],
        'moshaf_name': reciter_info['moshaf_name'],
        'server': reciter_info['server'],
        'collected_at': datetime.now().isoformat(),
        'surahs': {}
    }
    
    successful = 0
    
    for surah_num in range(1, 115):
        timings = get_surah_timings(reciter_id, surah_num)
        
        if timings:
            all_data['surahs'][str(surah_num)] = {
                'ayat_count': len(timings),
                'timings': timings
            }
            successful += 1
        
        time.sleep(0.08)
    
    all_data['stats'] = {
        'successful_surahs': successful,
        'total_ayat': sum(s['ayat_count'] for s in all_data['surahs'].values())
    }
    
    return all_data

def main():
    print("=" * 70)
    print("جمع بيانات جميع القراء مع التوقيتات")
    print("=" * 70)
    
    # تحميل قائمة القراء مع التوقيتات
    reciters_file = OUTPUT_DIR / "reciters_with_timings.json"
    
    if not reciters_file.exists():
        print("خطأ: يجب تشغيل find_all_reciters_with_timings.py أولاً")
        return
    
    with open(reciters_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    reciters = data['reciters']
    print(f"عدد القراء: {len(reciters)}")
    
    # تصنيف حسب الرواية
    riwayat_map = {
        'حفص': 'hafs',
        'ورش': 'warsh',
        'قالون': 'qaloun',
        'الدوري': 'douri',
        'شعبة': 'shuba',
        'السوسي': 'sousi'
    }
    
    summary = {
        'collected_at': datetime.now().isoformat(),
        'reciters': []
    }
    
    collected_ids = set()  # لتجنب التكرار
    
    for i, reciter in enumerate(reciters):
        # تخطي إذا تم جمعه من قبل
        unique_key = f"{reciter['reciter_id']}_{reciter['moshaf_id']}"
        if unique_key in collected_ids:
            continue
        collected_ids.add(unique_key)
        
        # تحديد الرواية
        riwayah_id = None
        for ar_name, en_id in riwayat_map.items():
            if ar_name in reciter['moshaf_name']:
                riwayah_id = en_id
                break
        
        if not riwayah_id:
            continue
        
        print(f"\n[{len(collected_ids)}/{len(reciters)}] {reciter['reciter_name']} - {reciter['moshaf_name']}")
        
        # جمع البيانات
        reciter_data = collect_reciter_data(reciter)
        
        if reciter_data['stats']['successful_surahs'] == 114:
            # حفظ البيانات
            output_dir = OUTPUT_DIR / riwayah_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{reciter['reciter_id']}_{reciter['moshaf_id']}_{reciter['reciter_name'].replace(' ', '_')}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(reciter_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✓ تم الحفظ ({reciter_data['stats']['total_ayat']} آية)")
            
            summary['reciters'].append({
                'reciter_id': reciter['reciter_id'],
                'reciter_name': reciter['reciter_name'],
                'moshaf_name': reciter['moshaf_name'],
                'riwayah': riwayah_id,
                'total_ayat': reciter_data['stats']['total_ayat'],
                'file': str(filepath)
            })
        else:
            print(f"   ✗ غير مكتمل ({reciter_data['stats']['successful_surahs']}/114)")
    
    # حفظ الملخص
    summary_path = OUTPUT_DIR / "complete_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # طباعة الملخص
    print("\n" + "=" * 70)
    print("الملخص النهائي")
    print("=" * 70)
    
    by_riwayah = {}
    for r in summary['reciters']:
        riwayah = r['riwayah']
        if riwayah not in by_riwayah:
            by_riwayah[riwayah] = []
        by_riwayah[riwayah].append(r['reciter_name'])
    
    for riwayah, names in by_riwayah.items():
        print(f"\n{riwayah}: {len(names)} قارئ")
        for name in names:
            print(f"   - {name}")
    
    print(f"\nإجمالي: {len(summary['reciters'])} قارئ")
    print(f"تم الحفظ في: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()



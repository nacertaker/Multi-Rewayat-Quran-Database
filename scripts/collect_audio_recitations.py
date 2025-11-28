"""
جمع التلاوات الصوتية من mp3quran.net API
يجمع فقط التلاوات التي لديها توقيتات لكل آية
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

def get_all_reciters():
    """الحصول على جميع القراء"""
    response = requests.get(f"{BASE_URL}/reciters", params={"language": "ar"})
    return response.json().get('reciters', [])

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
        print(f"      خطأ: {e}")
        return None

def check_reciter_has_timings(reciter_id, sample_surahs=[1, 2, 114]):
    """التحقق من أن القارئ لديه توقيتات"""
    for surah in sample_surahs:
        timings = get_surah_timings(reciter_id, surah)
        if not timings:
            return False
    return True

def classify_reciters_by_riwayah(reciters):
    """تصنيف القراء حسب الرواية"""
    
    riwayat = {
        'hafs': {'name': 'حفص عن عاصم', 'keywords': ['حفص'], 'reciters': []},
        'warsh': {'name': 'ورش عن نافع', 'keywords': ['ورش'], 'reciters': []},
        'qaloun': {'name': 'قالون عن نافع', 'keywords': ['قالون'], 'reciters': []},
        'douri': {'name': 'الدوري عن أبي عمرو', 'keywords': ['الدوري', 'دوري'], 'reciters': []},
        'shuba': {'name': 'شعبة عن عاصم', 'keywords': ['شعبة'], 'reciters': []},
        'sousi': {'name': 'السوسي عن أبي عمرو', 'keywords': ['السوسي', 'سوسي'], 'reciters': []},
    }
    
    for reciter in reciters:
        for moshaf in reciter.get('moshaf', []):
            moshaf_name = moshaf.get('name', '')
            
            # تحديد الرواية
            for riwayah_id, riwayah_data in riwayat.items():
                for keyword in riwayah_data['keywords']:
                    if keyword in moshaf_name:
                        riwayah_data['reciters'].append({
                            'reciter_id': reciter['id'],
                            'reciter_name': reciter['name'],
                            'moshaf_id': moshaf['id'],
                            'moshaf_name': moshaf_name,
                            'server': moshaf['server'],
                            'surah_total': moshaf.get('surah_total', 0),
                            'surah_list': moshaf.get('surah_list', '')
                        })
                        break
    
    return riwayat

def collect_reciter_timings(reciter_info, max_surahs=114):
    """جمع توقيتات جميع السور لقارئ معين"""
    
    reciter_id = reciter_info['reciter_id']
    reciter_name = reciter_info['reciter_name']
    
    print(f"\n   جاري جمع توقيتات: {reciter_name}")
    
    all_timings = {
        'reciter_id': reciter_id,
        'reciter_name': reciter_name,
        'moshaf_id': reciter_info['moshaf_id'],
        'moshaf_name': reciter_info['moshaf_name'],
        'server': reciter_info['server'],
        'collected_at': datetime.now().isoformat(),
        'surahs': {}
    }
    
    successful_surahs = 0
    failed_surahs = []
    
    for surah_num in range(1, max_surahs + 1):
        timings = get_surah_timings(reciter_id, surah_num)
        
        if timings:
            all_timings['surahs'][str(surah_num)] = {
                'ayat_count': len(timings),
                'timings': timings
            }
            successful_surahs += 1
            
            if surah_num % 20 == 0:
                print(f"      تم جمع {surah_num} سورة...")
        else:
            failed_surahs.append(surah_num)
        
        # تأخير بسيط لتجنب حظر API
        time.sleep(0.1)
    
    all_timings['stats'] = {
        'successful_surahs': successful_surahs,
        'failed_surahs': failed_surahs,
        'total_ayat': sum(s['ayat_count'] for s in all_timings['surahs'].values())
    }
    
    print(f"      ✓ تم جمع {successful_surahs}/114 سورة ({all_timings['stats']['total_ayat']} آية)")
    
    return all_timings

def save_reciter_data(reciter_data, riwayah_id):
    """حفظ بيانات القارئ"""
    
    output_dir = OUTPUT_DIR / riwayah_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{reciter_data['reciter_id']}_{reciter_data['reciter_name'].replace(' ', '_')}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(reciter_data, f, ensure_ascii=False, indent=2)
    
    return filepath

def main():
    print("=" * 70)
    print("جمع التلاوات الصوتية من mp3quran.net")
    print("=" * 70)
    
    # 1. الحصول على القراء
    print("\n1. جاري تحميل قائمة القراء...")
    reciters = get_all_reciters()
    print(f"   تم تحميل {len(reciters)} قارئ")
    
    # 2. تصنيف حسب الرواية
    print("\n2. تصنيف القراء حسب الرواية...")
    riwayat = classify_reciters_by_riwayah(reciters)
    
    for riwayah_id, riwayah_data in riwayat.items():
        complete = [r for r in riwayah_data['reciters'] if r['surah_total'] == 114]
        print(f"   {riwayah_data['name']}: {len(complete)} قارئ كامل")
    
    # 3. جمع البيانات لكل رواية
    print("\n3. جمع التوقيتات...")
    
    summary = {
        'collected_at': datetime.now().isoformat(),
        'riwayat': {}
    }
    
    for riwayah_id, riwayah_data in riwayat.items():
        print(f"\n{'='*50}")
        print(f"الرواية: {riwayah_data['name']}")
        print(f"{'='*50}")
        
        # فلترة القراء الكاملين
        complete_reciters = [r for r in riwayah_data['reciters'] if r['surah_total'] == 114]
        
        if not complete_reciters:
            print("   لا يوجد قراء كاملين لهذه الرواية")
            continue
        
        riwayah_summary = {
            'name': riwayah_data['name'],
            'reciters': []
        }
        
        # جمع بيانات لأول 3 قراء فقط (للاختبار)
        # يمكن تغييرها لجمع جميع القراء
        max_reciters = 3
        
        for i, reciter_info in enumerate(complete_reciters[:max_reciters]):
            print(f"\n   [{i+1}/{min(len(complete_reciters), max_reciters)}] {reciter_info['reciter_name']}")
            
            # التحقق من وجود توقيتات
            print(f"      جاري التحقق من التوقيتات...")
            has_timings = check_reciter_has_timings(reciter_info['reciter_id'])
            
            if not has_timings:
                print(f"      ✗ لا توجد توقيتات لهذا القارئ")
                continue
            
            # جمع جميع التوقيتات
            reciter_data = collect_reciter_timings(reciter_info)
            
            # حفظ البيانات
            if reciter_data['stats']['successful_surahs'] == 114:
                filepath = save_reciter_data(reciter_data, riwayah_id)
                print(f"      ✓ تم الحفظ في: {filepath}")
                
                riwayah_summary['reciters'].append({
                    'reciter_id': reciter_info['reciter_id'],
                    'reciter_name': reciter_info['reciter_name'],
                    'total_ayat': reciter_data['stats']['total_ayat'],
                    'file': str(filepath)
                })
            else:
                print(f"      ⚠ القارئ غير مكتمل، تم تخطيه")
        
        summary['riwayat'][riwayah_id] = riwayah_summary
    
    # 4. حفظ الملخص
    summary_path = OUTPUT_DIR / "summary.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print("الملخص النهائي")
    print(f"{'='*70}")
    
    total_reciters = 0
    for riwayah_id, riwayah_data in summary['riwayat'].items():
        count = len(riwayah_data.get('reciters', []))
        total_reciters += count
        print(f"   {riwayah_data['name']}: {count} قارئ")
    
    print(f"\n   إجمالي القراء: {total_reciters}")
    print(f"   تم الحفظ في: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()



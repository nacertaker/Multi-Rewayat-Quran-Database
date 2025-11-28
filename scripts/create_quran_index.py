"""
إنشاء فهرس شامل للسور والأجزاء والأحزاب لكل رواية
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# مسارات ملفات الروايات
RIWAYAT = {
    'hafs': 'UthmanicHafs_v2-0/UthmanicHafs_v2-0 data/HafsData_v2-0.json',
    'douri': 'UthmanicDouri_v2-0/UthmanicDouri_v2-0 data/DouriData_v2-0.json',
    'warsh': 'UthmanicWarsh_v2-1/UthmanicWarsh_v2-1 data/WarshData_v2-1.json',
    'qaloun': 'UthmanicQaloun_v2/UthmanicQaloun_v2-1 data/QalounData_v2-1.json',
    'shuba': 'UthmanicShuba_v2-0/UthmanicShuba_v2-0 data/ShubaData_v2-0.json',
    'sousi': 'UthmanicSousi_v2/UthmanicSousi_v2-0 data/SousiData_v2-0.json'
}

RIWAYAT_NAMES = {
    'hafs': 'حفص عن عاصم',
    'douri': 'الدوري عن أبي عمرو',
    'warsh': 'ورش عن نافع',
    'qaloun': 'قالون عن نافع',
    'shuba': 'شعبة عن عاصم',
    'sousi': 'السوسي عن أبي عمرو'
}

def create_index_for_riwayah(riwayah_key, json_path):
    """إنشاء فهرس لرواية واحدة"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # فهرس السور
    surahs = {}
    # فهرس الأجزاء
    juzs = defaultdict(lambda: {
        'start_surah': None,
        'start_ayah': None,
        'start_page': None,
        'end_surah': None,
        'end_ayah': None,
        'end_page': None,
        'ayat_count': 0
    })
    
    # جمع البيانات
    for ayah in data:
        sura_no = ayah['sura_no']
        sura_name_ar = ayah['sura_name_ar'].strip()
        sura_name_en = ayah['sura_name_en']
        aya_no = ayah['aya_no']
        page = ayah['page']
        jozz = ayah['jozz']
        
        # إضافة السورة إذا لم تكن موجودة
        if sura_no not in surahs:
            surahs[sura_no] = {
                'number': sura_no,
                'name_ar': sura_name_ar,
                'name_en': sura_name_en,
                'start_page': page,
                'end_page': page,
                'ayat_count': 0,
                'juz_start': jozz
            }
        
        # تحديث بيانات السورة
        surahs[sura_no]['ayat_count'] += 1
        surahs[sura_no]['end_page'] = page
        surahs[sura_no]['juz_end'] = jozz
        
        # تحديث بيانات الجزء
        juz = juzs[jozz]
        juz['ayat_count'] += 1
        
        if juz['start_surah'] is None:
            juz['start_surah'] = sura_no
            juz['start_ayah'] = aya_no
            juz['start_page'] = page
        
        juz['end_surah'] = sura_no
        juz['end_ayah'] = aya_no
        juz['end_page'] = page
    
    # تحويل الأجزاء إلى قائمة
    juzs_list = []
    for juz_no in sorted(juzs.keys()):
        juz_data = juzs[juz_no]
        juz_data['number'] = juz_no
        juzs_list.append(juz_data)
    
    # تحويل السور إلى قائمة
    surahs_list = [surahs[i] for i in sorted(surahs.keys())]
    
    # حساب الأحزاب (كل جزء = حزبين)
    ahzab = []
    for juz in juzs_list:
        hizb1 = juz['number'] * 2 - 1
        hizb2 = juz['number'] * 2
        ahzab.append({
            'number': hizb1,
            'juz': juz['number'],
            'quarter': 1
        })
        ahzab.append({
            'number': hizb2,
            'juz': juz['number'],
            'quarter': 2
        })
    
    return {
        'riwayah': riwayah_key,
        'riwayah_name': RIWAYAT_NAMES[riwayah_key],
        'total_surahs': len(surahs_list),
        'total_ayat': sum(s['ayat_count'] for s in surahs_list),
        'total_juzs': len(juzs_list),
        'total_pages': max(s['end_page'] for s in surahs_list),
        'surahs': surahs_list,
        'juzs': juzs_list
    }

def main():
    print("=" * 70)
    print("إنشاء فهرس السور والأجزاء والأحزاب لكل رواية")
    print("=" * 70)
    
    output_dir = Path("data/quran_index")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_indexes = {}
    
    for riwayah_key, json_path in RIWAYAT.items():
        print(f"\n{RIWAYAT_NAMES[riwayah_key]}...")
        
        if not Path(json_path).exists():
            print(f"   ⚠ الملف غير موجود: {json_path}")
            continue
        
        index = create_index_for_riwayah(riwayah_key, json_path)
        all_indexes[riwayah_key] = index
        
        # حفظ فهرس الرواية
        output_path = output_dir / f"{riwayah_key}_index.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {index['total_surahs']} سورة")
        print(f"   ✓ {index['total_ayat']} آية")
        print(f"   ✓ {index['total_juzs']} جزء")
        print(f"   ✓ {index['total_pages']} صفحة")
    
    # حفظ الفهرس الموحد
    unified_path = output_dir / "all_riwayat_index.json"
    with open(unified_path, 'w', encoding='utf-8') as f:
        json.dump(all_indexes, f, ensure_ascii=False, indent=2)
    
    # إنشاء ملخص مقارنة
    print("\n" + "=" * 70)
    print("ملخص المقارنة بين الروايات")
    print("=" * 70)
    
    print(f"\n{'الرواية':<25} {'السور':<8} {'الآيات':<10} {'الأجزاء':<8} {'الصفحات':<10}")
    print("-" * 70)
    
    for key, idx in all_indexes.items():
        print(f"{idx['riwayah_name']:<25} {idx['total_surahs']:<8} {idx['total_ayat']:<10} {idx['total_juzs']:<8} {idx['total_pages']:<10}")
    
    # التحقق من التلاوات
    print("\n" + "=" * 70)
    print("التلاوات المتوفرة لكل رواية")
    print("=" * 70)
    
    audio_summary_path = Path("data/audio_recitations/reciters_with_timings.json")
    if audio_summary_path.exists():
        with open(audio_summary_path, 'r', encoding='utf-8') as f:
            audio_data = json.load(f)
        
        by_riwayah = audio_data.get('by_riwayah', {})
        
        riwayah_map = {
            'حفص': 'hafs',
            'ورش': 'warsh',
            'قالون': 'qaloun',
            'الدوري': 'douri',
            'شعبة': 'shuba',
            'السوسي': 'sousi'
        }
        
        for ar_name, key in riwayah_map.items():
            reciters = by_riwayah.get(ar_name, [])
            status = "✓" if reciters else "✗"
            count = len(reciters)
            print(f"   {status} {RIWAYAT_NAMES[key]}: {count} قارئ")
            if reciters:
                for rec in reciters[:3]:
                    print(f"      - {rec['reciter_name']}")
                if len(reciters) > 3:
                    print(f"      ... و {len(reciters) - 3} آخرين")
    
    print(f"\nتم الحفظ في: {output_dir}")

if __name__ == "__main__":
    main()


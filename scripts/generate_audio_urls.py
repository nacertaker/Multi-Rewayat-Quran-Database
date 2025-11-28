"""
إنشاء روابط تحميل الملفات الصوتية لجميع القراء
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = Path("data/audio_recitations")

def main():
    print("=" * 70)
    print("إنشاء روابط تحميل الملفات الصوتية")
    print("=" * 70)
    
    # تحميل الملخص
    summary_path = OUTPUT_DIR / "complete_summary.json"
    
    if not summary_path.exists():
        print("خطأ: يجب تشغيل collect_all_reciters_with_timings.py أولاً")
        return
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    all_urls = {
        'generated_at': summary['collected_at'],
        'reciters': []
    }
    
    for reciter in summary['reciters']:
        # تحميل بيانات القارئ
        reciter_file = Path(reciter['file'])
        
        if not reciter_file.exists():
            continue
        
        with open(reciter_file, 'r', encoding='utf-8') as f:
            reciter_data = json.load(f)
        
        server = reciter_data['server']
        
        # إنشاء روابط السور
        surah_urls = []
        for surah_num in range(1, 115):
            url = f"{server}{surah_num:03d}.mp3"
            surah_urls.append({
                'surah': surah_num,
                'url': url
            })
        
        all_urls['reciters'].append({
            'reciter_id': reciter['reciter_id'],
            'reciter_name': reciter['reciter_name'],
            'moshaf_name': reciter['moshaf_name'],
            'riwayah': reciter['riwayah'],
            'server': server,
            'surahs': surah_urls
        })
    
    # حفظ الروابط
    urls_path = OUTPUT_DIR / "audio_urls.json"
    with open(urls_path, 'w', encoding='utf-8') as f:
        json.dump(all_urls, f, ensure_ascii=False, indent=2)
    
    print(f"\nتم إنشاء روابط لـ {len(all_urls['reciters'])} قارئ")
    print(f"تم الحفظ في: {urls_path}")
    
    # عرض مثال
    print("\n" + "=" * 70)
    print("مثال على الروابط:")
    print("=" * 70)
    
    if all_urls['reciters']:
        reciter = all_urls['reciters'][0]
        print(f"\nالقارئ: {reciter['reciter_name']}")
        print(f"الرواية: {reciter['moshaf_name']}")
        print(f"\nأول 5 سور:")
        for surah in reciter['surahs'][:5]:
            print(f"   سورة {surah['surah']}: {surah['url']}")

if __name__ == "__main__":
    main()



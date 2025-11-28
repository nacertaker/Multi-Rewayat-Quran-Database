"""
الاستخراج النهائي: نستخدم آخر آية في كل صفحة كحد أقصى
"""

import docx
import json
import re
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SURA_NAMES_PATH = BASE_DIR / 'surahs_name.json'

def extract_aya_numbers(text):
    """استخراج أرقام الآيات من النص - يدعم جميع الروايات"""
    if not text or text.strip() == '':
        return []
    
    # الأرقام العربية الشرقية (المستخدمة في معظم الروايات)
    arabic_numbers = {
        '٠': 0, '١': 1, '٢': 2, '٣': 3, '٤': 4,
        '٥': 5, '٦': 6, '٧': 7, '٨': 8, '٩': 9
    }
    
    aya_numbers = []
    
    # البحث عن الأرقام العربية الشرقية
    matches = re.findall(r'[٠-٩]+', text)
    
    for match in matches:
        number = 0
        for char in match:
            number = number * 10 + arabic_numbers.get(char, 0)
        if number > 0:
            aya_numbers.append(number)
    
    # إذا لم نجد أرقام، نبحث عن الأرقام الهندية (المستخدمة في بعض الروايات)
    if not aya_numbers:
        # الأرقام الهندية العربية
        hindi_numbers = {
            '۰': 0, '۱': 1, '۲': 2, '۳': 3, '۴': 4,
            '۵': 5, '۶': 6, '۷': 7, '۸': 8, '۹': 9
        }
        matches = re.findall(r'[۰-۹]+', text)
        for match in matches:
            number = 0
            for char in match:
                number = number * 10 + hindi_numbers.get(char, 0)
            if number > 0:
                aya_numbers.append(number)
    
    return aya_numbers

def is_sura_header(text):
    return text.startswith('سُورَةُ')

def is_basmala(text):
    """التحقق من البسملة - يدعم جميع الروايات"""
    # أنماط البسملة المختلفة
    basmala_patterns = [
        'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ',  # حفص
        'بِسۡمِ اِ۬للَّهِ اِ۬لرَّحۡمَٰنِ اِ۬لرَّحِيمِ',  # الدوري
        'بِسْمِ اِ۬للَّهِ اِ۬لرَّحْمَٰنِ اِ۬لرَّحِيمِ',  # ورش
        'بسم الله الرحمن الرحيم',  # عام
    ]
    
    # التحقق من وجود أي نمط من البسملة
    text_normalized = text.replace('ٱ', 'ا').replace('اِ۬', 'ا').replace('اُ۬', 'ا')
    has_basmala = any(pattern in text for pattern in basmala_patterns) or 'بسم' in text_normalized and 'الله' in text_normalized and 'الرحم' in text_normalized
    
    # التأكد من عدم وجود أرقام آيات
    has_numbers = any(c in text for c in '٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹')
    
    return has_basmala and not has_numbers

def is_empty_line(text):
    cleaned = text.strip()
    cleaned = re.sub(r'[\u200B-\u200D\uFEFF]', '', cleaned)
    return len(cleaned) == 0

def extract_sura_name(header_text):
    name = header_text.replace('سُورَةُ ', '')
    return name.strip()

def normalize_sura_name(name):
    """تطبيع اسم السورة لإزالة الاختلافات بين الروايات"""
    name = name.replace('سُورَةُ ', '')
    
    # إزالة أل التعريف بأشكالها المختلفة
    name = name.replace('ٱل', 'ال').replace('اُ۬ل', 'ال').replace('اَ۬ل', 'ال')
    name = name.replace('ٱ', 'ا').replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    name = name.replace('اُ۬', 'ا').replace('اَ۬', 'ا').replace('اِ۬', 'ا')
    
    # تحويل الهمزة إلى ألف (مهم لرواية ورش)
    name = name.replace('ء', 'ا')
    
    # إزالة حرف التطويل (ـ)
    name = name.replace('ـ', '')
    
    # إزالة التشكيل والحروف الخاصة
    # حذف التشكيل العادي
    name = re.sub(r'[\u064B-\u065F\u0670]', '', name)
    # حذف علامات الضبط الخاصة بالروايات (مثل ۬ و ۪ و ۖ وغيرها)
    name = re.sub(r'[\u06D6-\u06ED]', '', name)
    # حذف السكون والشدة وغيرها
    name = re.sub(r'[\u0610-\u061A]', '', name)
    
    # إزالة المسافات الزائدة
    name = ' '.join(name.split())
    name = name.strip()
    return name

def load_json_data(json_path):
    """تحميل بيانات JSON وإنشاء خرائط"""
    print("جاري تحميل JSON الأصلي...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # خريطة: (sura_no, aya_no) -> page
    aya_to_page = {}
    
    for item in data:
        sura_no = item['sura_no']
        aya_no = item['aya_no']
        page = item['page']
        
        if '-' in str(page):
            page = int(page.split('-')[0])
        else:
            page = int(page)
        
        aya_to_page[(sura_no, aya_no)] = page
    
    print(f"تم تحميل {len(aya_to_page)} آية")
    return aya_to_page

def deep_normalize(name):
    """تطبيع عميق لأسماء السور - يزيل كل الاختلافات بين الروايات"""
    name = normalize_sura_name(name)
    
    # تحويل الألف المقصورة والياء إلى نفس الحرف
    name = name.replace('ى', 'ي')
    
    # تحويل الهمزة على الواو إلى واو (المؤمنون -> المومنون)
    name = name.replace('ؤ', 'و')
    
    # إزالة المسافات
    name = name.replace(' ', '')
    
    return name

# خريطة يدوية للسور المشكلة في الروايات المختلفة
# الاسم المطبّع من الرواية -> رقم السورة
MANUAL_SURA_MAP = {
    # آل عمران (3)
    'اال عمران': 3,
    'ءال عمران': 3,
    # الأنعام (6)
    'الانعام': 6,
    'الانعم': 6,
    # إبراهيم (14)
    'ابراهيم': 14,
    'ابرهيم': 14,
    # المؤمنون (23)
    'المومنون': 23,
    'المؤمنون': 23,
    # لقمان (31)
    'لقمان': 31,
    'لقمن': 31,
    # الصافات (37)
    'الصافات': 37,
    'الصفت': 37,
    'الصفات': 37,
    # الشورى (42)
    'الشوري': 42,
    'الشورى': 42,
    # الذاريات (51)
    'الذاريات': 51,
    'الذريت': 51,
    'الذريات': 51,
    # المنافقون (63)
    'المنافقون': 63,
    'المنفقون': 63,
    # القيامة (75)
    'القيامة': 75,
    'القيمة': 75,
    # الإنسان (76)
    'الانسان': 76,
    'الانسن': 76,
    # المرسلات (77)
    'المرسلات': 77,
    'المرسلت': 77,
    # النازعات (79)
    'النازعات': 79,
    'النزعت': 79,
    'النزعات': 79,
    # الأعلى (87)
    'الاعلي': 87,
    'الاعلى': 87,
    # الغاشية (88)
    'الغاشية': 88,
    'الغشية': 88,
    # الليل (92)
    'الليل': 92,
    'اليل': 92,
    # الضحى (93)
    'الضحي': 93,
    'الضحى': 93,
    # العاديات (100)
    'العاديات': 100,
    'العديت': 100,
    'العديات': 100,
    # الكوثر (108)
    'الكوثر': 108,
    # الكافرون (109)
    'الكافرون': 109,
    'الكفرون': 109,
}

def load_sura_map(sura_path=SURA_NAMES_PATH):
    print("جاري تحميل أسماء السور...")
    with open(sura_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sura_map = {}
    sura_map_deep = {}
    
    for sura in data['data']['surahs']:
        name = sura['name']
        name_normalized = normalize_sura_name(name)
        name_deep = deep_normalize(name)
        
        sura_map[name_normalized] = sura['number']
        sura_map_deep[name_deep] = sura['number']
    
    print(f"تم تحميل {len(sura_map)} سورة")
    return sura_map, sura_map_deep

def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="استخراج الأسطر مع مطابقة الصفحات للروايات المختلفة"
    )
    parser.add_argument(
        "--docx",
        required=True,
        help="مسار ملف Word للرواية"
    )
    parser.add_argument(
        "--json",
        required=True,
        help="مسار ملف JSON للرواية"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="مسار ملف JSON الناتج"
    )
    parser.add_argument(
        "--label",
        default="رواية",
        help="اسم الرواية (لأغراض العرض فقط)"
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    docx_path = Path(args.docx).resolve()
    json_path = Path(args.json).resolve()
    output_path = Path(args.output).resolve()
    label = args.label

    print("=" * 60)
    print(f"الاستخراج النهائي - {label}")
    print("=" * 60)
    
    # تحميل البيانات المرجعية
    aya_to_page = load_json_data(json_path)
    sura_map, sura_map_deep = load_sura_map()
    
    # فتح ملف Word
    print(f"\nجاري فتح الملف: {docx_path}")
    
    try:
        document = docx.Document(str(docx_path))
    except Exception as e:
        print(f"خطأ في فتح الملف: {e}")
        return
    
    print(f"تم فتح الملف بنجاح")
    
    # استخراج الأسطر
    lines = []
    pending_lines = []
    current_sura = ""
    current_sura_no = 0
    current_page = 0
    current_aya_numbers = []
    
    print("\nجاري استخراج الأسطر...")
    
    for para_idx, para in enumerate(document.paragraphs):
        full_text = para.text
        
        if is_empty_line(full_text):
            continue
        
        para_lines = full_text.split('\n')
        
        for line_text in para_lines:
            if is_empty_line(line_text):
                continue
            
            line_text = line_text.strip()
            
            if is_sura_header(line_text):
                # عند حدوث عنوان جديد، نتأكد من تفريغ الأسطر المعلقة
                if pending_lines:
                    for pending in pending_lines:
                        pending['page'] = current_page
                        pending['aya_numbers'] = current_aya_numbers
                    lines.extend(pending_lines)
                    pending_lines = []
                
                # عنوان سورة جديدة
                current_sura = extract_sura_name(line_text)
                current_sura_normalized = normalize_sura_name(current_sura)
                current_sura_deep = deep_normalize(current_sura)
                
                # محاولة المطابقة: يدوية أولاً، ثم عادية، ثم عميقة
                current_sura_no = MANUAL_SURA_MAP.get(current_sura_normalized, 0)
                if current_sura_no == 0:
                    current_sura_no = sura_map.get(current_sura_normalized, 0)
                if current_sura_no == 0:
                    current_sura_no = sura_map_deep.get(current_sura_deep, 0)
                if current_sura_no == 0:
                    current_sura_no = MANUAL_SURA_MAP.get(current_sura_deep, 0)
                
                # تحديد الصفحة
                page = aya_to_page.get((current_sura_no, 1), 1)
                current_page = page
                
                lines.append({
                    'page': page,
                    'sura': current_sura,
                    'sura_no': current_sura_no,
                    'type': 'header',
                    'text': line_text
                })
                
            elif is_basmala(line_text):
                # بسملة
                if pending_lines:
                    for pending in pending_lines:
                        pending['page'] = current_page
                        pending['aya_numbers'] = current_aya_numbers
                    lines.extend(pending_lines)
                    pending_lines = []
                
                lines.append({
                    'page': current_page,
                    'sura': current_sura,
                    'sura_no': current_sura_no,
                    'type': 'basmala',
                    'text': line_text,
                    'aya_numbers': []
                })
                
            else:
                # آيات القرآن
                aya_numbers = extract_aya_numbers(line_text)
                
                if aya_numbers and current_sura_no > 0:
                    first_aya = aya_numbers[0]
                    page = aya_to_page.get((current_sura_no, first_aya), current_page or 1)
                    
                    # تفريغ الأسطر المعلقة قبل إضافة السطر الحالي
                    if pending_lines:
                        for pending in pending_lines:
                            pending['page'] = page
                            pending['aya_numbers'] = aya_numbers
                        lines.extend(pending_lines)
                        pending_lines = []
                    
                    current_page = page
                    current_aya_numbers = aya_numbers
                    
                    lines.append({
                        'page': page,
                        'sura': current_sura,
                        'sura_no': current_sura_no,
                        'type': 'ayat',
                        'text': line_text,
                        'aya_numbers': aya_numbers
                    })
                else:
                    # سطر بدون أرقام آيات -> نضيفه لقائمة الانتظار
                    pending_lines.append({
                        'page': None,
                        'sura': current_sura,
                        'sura_no': current_sura_no,
                        'type': 'ayat',
                        'text': line_text,
                        'aya_numbers': []
                    })
        
        if (para_idx + 1) % 100 == 0:
            print(f"تم معالجة {para_idx + 1} فقرة...")
    
    # إذا تبقت أسطر معلقة في النهاية، ننسبها لآخر آية معروفة
    if pending_lines:
        for pending in pending_lines:
            pending['page'] = current_page
            pending['aya_numbers'] = current_aya_numbers
        lines.extend(pending_lines)
        pending_lines = []
    
    print(f"\nتم استخراج {len(lines)} سطر")
    
    # إعادة ترقيم الأسطر لكل صفحة
    print("\nجاري إعادة ترقيم الأسطر...")
    current_page = 0
    line_in_page = 0
    
    for line in lines:
        if line['page'] != current_page:
            current_page = line['page']
            line_in_page = 1
        
        line['line'] = line_in_page
        line_in_page += 1
    
    # حفظ النتيجة
    print(f"\nجاري حفظ البيانات في {output_path}...")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(lines, f, ensure_ascii=False, indent=2)
    
    print("تم الحفظ بنجاح!")
    
    # إحصائيات
    print("\n" + "=" * 60)
    print("الإحصائيات:")
    print("=" * 60)
    
    pages = set(l['page'] for l in lines)
    print(f"عدد الصفحات: {len(pages)}")
    print(f"إجمالي الأسطر: {len(lines)}")
    
    # عرض الصفحة 2
    print("\n" + "=" * 60)
    print("الصفحة 2:")
    print("=" * 60)
    page2 = [l for l in lines if l['page'] == 2]
    print(f"عدد الأسطر: {len(page2)}")
    for line in page2:
        aya_str = f" (آيات: {line['aya_numbers']})" if line.get('aya_numbers') else ""
        print(f"سطر {line['line']}{aya_str}: {line['text'][:60]}...")
    
    # عرض الصفحة 3
    print("\n" + "=" * 60)
    print("الصفحة 3:")
    print("=" * 60)
    page3 = [l for l in lines if l['page'] == 3]
    print(f"عدد الأسطر: {len(page3)}")
    for line in page3[:10]:
        aya_str = f" (آيات: {line['aya_numbers']})" if line.get('aya_numbers') else ""
        print(f"سطر {line['line']}{aya_str}: {line['text'][:60]}...")

if __name__ == "__main__":
    main()


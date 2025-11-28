"""
خادم API بسيط للقرآن الكريم متعدد الروايات
يستخدم Flask لتقديم البيانات من قاعدة SQLite
"""

import sqlite3
import json
import sys
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# إضافة المسار الرئيسي
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__, static_folder='.')
CORS(app)

DATABASE_PATH = Path(__file__).parent.parent / "quran_database.db"

def get_db():
    """الحصول على اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """تحويل صف قاعدة البيانات إلى قاموس"""
    return dict(zip(row.keys(), row))

# ==================== الصفحات الثابتة ====================

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# ==================== API الروايات ====================

@app.route('/api/riwayat')
def get_riwayat():
    """الحصول على قائمة الروايات"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM riwayat')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

@app.route('/api/riwayat/<key>')
def get_riwayah(key):
    """الحصول على معلومات رواية محددة"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM riwayat WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict_from_row(row))
    return jsonify({'error': 'Riwayah not found'}), 404

# ==================== API السور ====================

@app.route('/api/surahs')
def get_surahs():
    """الحصول على قائمة السور"""
    riwayah = request.args.get('riwayah', 'hafs')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM surahs WHERE riwayah_key = ? ORDER BY number
    ''', (riwayah,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

@app.route('/api/surahs/<int:number>')
def get_surah(number):
    """الحصول على معلومات سورة محددة"""
    riwayah = request.args.get('riwayah', 'hafs')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM surahs WHERE number = ? AND riwayah_key = ?
    ''', (number, riwayah))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict_from_row(row))
    return jsonify({'error': 'Surah not found'}), 404

# ==================== API الآيات ====================

@app.route('/api/ayat')
def get_ayat():
    """الحصول على الآيات"""
    riwayah = request.args.get('riwayah', 'hafs')
    sura = request.args.get('sura')
    page = request.args.get('page')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if sura:
        cursor.execute('''
            SELECT * FROM ayat WHERE sura_no = ? AND riwayah_key = ? ORDER BY aya_no
        ''', (sura, riwayah))
    elif page:
        cursor.execute('''
            SELECT * FROM ayat WHERE page = ? AND riwayah_key = ? ORDER BY sura_no, aya_no
        ''', (page, riwayah))
    else:
        cursor.execute('''
            SELECT * FROM ayat WHERE riwayah_key = ? LIMIT 100
        ''', (riwayah,))
    
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

@app.route('/api/ayat/<int:sura>/<int:aya>')
def get_ayah(sura, aya):
    """الحصول على آية محددة"""
    riwayah = request.args.get('riwayah', 'hafs')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ayat WHERE sura_no = ? AND aya_no = ? AND riwayah_key = ?
    ''', (sura, aya, riwayah))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict_from_row(row))
    return jsonify({'error': 'Ayah not found'}), 404

# ==================== API الأسطر (للعرض المطابق للمصحف) ====================

@app.route('/api/lines')
def get_lines():
    """الحصول على الأسطر"""
    riwayah = request.args.get('riwayah', 'hafs')
    page = request.args.get('page', 1, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM lines WHERE page = ? AND riwayah_key = ? ORDER BY line_number
    ''', (page, riwayah))
    rows = cursor.fetchall()
    conn.close()
    
    lines = []
    for row in rows:
        line = dict_from_row(row)
        # تحويل aya_numbers من JSON string إلى list
        if line.get('aya_numbers'):
            try:
                line['aya_numbers'] = json.loads(line['aya_numbers'])
            except:
                line['aya_numbers'] = []
        lines.append(line)
    
    return jsonify(lines)

@app.route('/api/page/<int:page_num>')
def get_page(page_num):
    """الحصول على صفحة كاملة"""
    riwayah = request.args.get('riwayah', 'hafs')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # الحصول على الأسطر
    cursor.execute('''
        SELECT * FROM lines WHERE page = ? AND riwayah_key = ? ORDER BY line_number
    ''', (page_num, riwayah))
    lines = cursor.fetchall()
    
    # الحصول على معلومات الصفحة
    cursor.execute('''
        SELECT DISTINCT sura_no, juz FROM ayat WHERE page = ? AND riwayah_key = ?
    ''', (page_num, riwayah))
    page_info = cursor.fetchall()
    
    conn.close()
    
    result = {
        'page': page_num,
        'riwayah': riwayah,
        'lines': [],
        'suras': [],
        'juz': None
    }
    
    for line in lines:
        line_dict = dict_from_row(line)
        if line_dict.get('aya_numbers'):
            try:
                line_dict['aya_numbers'] = json.loads(line_dict['aya_numbers'])
            except:
                line_dict['aya_numbers'] = []
        result['lines'].append(line_dict)
    
    for info in page_info:
        result['suras'].append(info['sura_no'])
        if info['juz']:
            result['juz'] = info['juz']
    
    return jsonify(result)

# ==================== API الأجزاء ====================

@app.route('/api/juzs')
def get_juzs():
    """الحصول على قائمة الأجزاء"""
    riwayah = request.args.get('riwayah', 'hafs')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM juzs WHERE riwayah_key = ? ORDER BY number
    ''', (riwayah,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

# ==================== API الأحزاب ====================

@app.route('/api/ahzab')
def get_ahzab():
    """الحصول على قائمة الأحزاب"""
    riwayah = request.args.get('riwayah', 'hafs')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ahzab WHERE riwayah_key = ? ORDER BY hizb_num
    ''', (riwayah,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

@app.route('/api/quarters')
def get_quarters():
    """الحصول على قائمة الأرباع"""
    riwayah = request.args.get('riwayah', 'hafs')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM quarters WHERE riwayah_key = ? ORDER BY quarter_num
    ''', (riwayah,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

# ==================== API التفسير ====================

@app.route('/api/tafseer/<int:sura>/<int:aya>')
def get_tafseer(sura, aya):
    """الحصول على تفسير آية"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tafseer WHERE sura_no = ? AND aya_no = ?
    ''', (sura, aya))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict_from_row(row))
    return jsonify({'error': 'Tafseer not found'}), 404

@app.route('/api/tafseer/<int:sura>')
def get_surah_tafseer(sura):
    """الحصول على تفسير سورة كاملة"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tafseer WHERE sura_no = ? ORDER BY aya_no
    ''', (sura,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

# ==================== API الترجمة ====================

@app.route('/api/translation/<int:sura>/<int:aya>')
def get_translation(sura, aya):
    """الحصول على ترجمة آية"""
    language = request.args.get('lang', 'en')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM translations WHERE sura_no = ? AND aya_no = ? AND language = ?
    ''', (sura, aya, language))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict_from_row(row))
    return jsonify({'error': 'Translation not found'}), 404

@app.route('/api/translation/<int:sura>')
def get_surah_translation(sura):
    """الحصول على ترجمة سورة كاملة"""
    language = request.args.get('lang', 'en')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM translations WHERE sura_no = ? AND language = ? ORDER BY aya_no
    ''', (sura, language))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

# ==================== API القراء ====================

@app.route('/api/reciters')
def get_reciters():
    """الحصول على قائمة القراء"""
    riwayah = request.args.get('riwayah')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if riwayah:
        cursor.execute('''
            SELECT * FROM reciters WHERE riwayah_key = ?
        ''', (riwayah,))
    else:
        cursor.execute('SELECT * FROM reciters')
    
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

@app.route('/api/timings/<int:reciter_id>/<int:sura>')
def get_timings(reciter_id, sura):
    """الحصول على توقيتات سورة لقارئ"""
    moshaf_id = request.args.get('moshaf_id', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    if moshaf_id:
        cursor.execute('''
            SELECT * FROM ayah_timings 
            WHERE reciter_id = ? AND moshaf_id = ? AND sura_no = ?
            ORDER BY aya_no
        ''', (reciter_id, moshaf_id, sura))
    else:
        cursor.execute('''
            SELECT * FROM ayah_timings 
            WHERE reciter_id = ? AND sura_no = ?
            ORDER BY aya_no
        ''', (reciter_id, sura))
    
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict_from_row(row) for row in rows])

# ==================== API البحث ====================

@app.route('/api/search')
def search():
    """البحث في القرآن"""
    query = request.args.get('q', '')
    riwayah = request.args.get('riwayah', 'hafs')
    limit = request.args.get('limit', 50, type=int)
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # البحث في النص الإملائي
    cursor.execute('''
        SELECT a.*, s.name_ar as sura_name 
        FROM ayat a
        JOIN surahs s ON a.sura_no = s.number AND a.riwayah_key = s.riwayah_key
        WHERE a.text_emlaey LIKE ? AND a.riwayah_key = ?
        LIMIT ?
    ''', (f'%{query}%', riwayah, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'query': query,
        'count': len(rows),
        'results': [dict_from_row(row) for row in rows]
    })

# ==================== API الإحصائيات ====================

@app.route('/api/stats')
def get_stats():
    """الحصول على إحصائيات قاعدة البيانات"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # عدد الروايات
    cursor.execute('SELECT COUNT(*) FROM riwayat')
    stats['riwayat_count'] = cursor.fetchone()[0]
    
    # عدد الآيات الإجمالي
    cursor.execute('SELECT COUNT(*) FROM ayat')
    stats['total_ayat'] = cursor.fetchone()[0]
    
    # عدد الأسطر
    cursor.execute('SELECT COUNT(*) FROM lines')
    stats['total_lines'] = cursor.fetchone()[0]
    
    # عدد التفاسير
    cursor.execute('SELECT COUNT(*) FROM tafseer')
    stats['tafseer_count'] = cursor.fetchone()[0]
    
    # عدد الترجمات
    cursor.execute('SELECT COUNT(*) FROM translations')
    stats['translations_count'] = cursor.fetchone()[0]
    
    # عدد القراء
    cursor.execute('SELECT COUNT(DISTINCT reciter_id) FROM reciters')
    stats['reciters_count'] = cursor.fetchone()[0]
    
    # عدد التوقيتات
    cursor.execute('SELECT COUNT(*) FROM ayah_timings')
    stats['timings_count'] = cursor.fetchone()[0]
    
    conn.close()
    return jsonify(stats)

if __name__ == '__main__':
    print("=" * 60)
    print("خادم API للقرآن الكريم متعدد الروايات")
    print("=" * 60)
    print(f"\nقاعدة البيانات: {DATABASE_PATH}")
    print(f"\nالرابط: http://localhost:5000")
    print("\nنقاط النهاية المتاحة:")
    print("  - GET /api/riwayat              - قائمة الروايات")
    print("  - GET /api/surahs               - قائمة السور")
    print("  - GET /api/page/<num>           - صفحة كاملة")
    print("  - GET /api/ayat?sura=X          - آيات سورة")
    print("  - GET /api/tafseer/<sura>/<aya> - التفسير")
    print("  - GET /api/translation/<sura>   - الترجمة")
    print("  - GET /api/reciters             - القراء")
    print("  - GET /api/search?q=...         - البحث")
    print("  - GET /api/stats                - الإحصائيات")
    print("\n" + "=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


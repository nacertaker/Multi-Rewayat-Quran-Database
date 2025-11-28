"""
اختبار بسيط للتحقق من أن قاعدة البيانات تعمل
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "quran_database.db"

if not db_path.exists():
    print("❌ خطأ: قاعدة البيانات غير موجودة!")
    print(f"   المسار المتوقع: {db_path}")
    exit(1)

print("✅ قاعدة البيانات موجودة")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # اختبار الروايات
    cursor.execute("SELECT COUNT(*) FROM riwayat")
    riwayat_count = cursor.fetchone()[0]
    print(f"✅ عدد الروايات: {riwayat_count}")
    
    # اختبار الآيات
    cursor.execute("SELECT COUNT(*) FROM ayat")
    ayat_count = cursor.fetchone()[0]
    print(f"✅ عدد الآيات: {ayat_count}")
    
    # اختبار الأسطر
    cursor.execute("SELECT COUNT(*) FROM lines")
    lines_count = cursor.fetchone()[0]
    print(f"✅ عدد الأسطر: {lines_count}")
    
    # اختبار التفسير
    cursor.execute("SELECT COUNT(*) FROM tafseer")
    tafseer_count = cursor.fetchone()[0]
    print(f"✅ عدد التفاسير: {tafseer_count}")
    
    # اختبار القراء
    cursor.execute("SELECT COUNT(*) FROM reciters")
    reciters_count = cursor.fetchone()[0]
    print(f"✅ عدد القراء: {reciters_count}")
    
    conn.close()
    print("\n✅ كل شيء يعمل بشكل صحيح!")
    
except Exception as e:
    print(f"❌ خطأ: {e}")
    exit(1)


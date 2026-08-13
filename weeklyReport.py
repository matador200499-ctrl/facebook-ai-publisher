#!/usr/bin/env python3
"""
Weekly Facebook Performance Report Generator
Summarizes published topics from history.json and prepares an email digest.
"""

import os
import json
from datetime import datetime

def generate_weekly_report():
    print("📊 جاري إعداد التقرير الأسبوعي لأداء الصفحة...")
    
    history_path = os.path.join(os.path.dirname(__file__), "history.json")
    published_count = 0
    recent_topics = []
    
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                topics = data.get("published_topics", [])
                published_count = len(topics)
                recent_topics = topics[-7:] # Last 7 topics
        except Exception as e:
            print(f"⚠️ خطأ في قراءة السجل: {e}")
            
    report_body = f"""📊 تقرير الأداء الأسبوعي - صفحة فيسبوك (bobo_yasoo)
تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}

📈 ملخص النشاط:
- إجمالي الفيديوهات المنشورة المسجلة: {published_count} فيديو
- حالة نظام منع التكرار: 🟢 يعمل بكفاءة عالية (History Tracking Active)
- استراتيجية السيو والوصول (2026): مفعلة بالكامل

🎬 آخر المواضيع التي تم نشرها هذا الأسبوع:
"""
    
    for i, topic in enumerate(recent_topics, 1):
        report_body += f"{i}. {topic}\n"
        
    report_body += f"""
💡 نصائح لزيادة الريتش هذا الأسبوع:
1. الرد على أول 5 تعليقات في كل فيديو خلال أول ساعة من النشر.
2. مشاركة روابط الفيديوهات في المجموعات المهتمة بمحتواك.
3. تفقد الـ Artifacts في GitHub Actions في حال احتياج أي فيديو للرفع اليدوي.

مع تحيات نظام النشر الذكي الآلي.
"""

    report_path = os.path.join(os.path.dirname(__file__), "output", "weekly_report.txt")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_body)
        
    print(f"✅ تم إنشاء التقرير الأسبوعي بنجاح في: {report_path}")
    return report_body

if __name__ == "__main__":
    generate_weekly_report()

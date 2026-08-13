#!/usr/bin/env python3
"""
Facebook Video Publisher - Main Entry Point
Generates video automatically and publishes to Facebook
"""

import os
import sys
import asyncio

import requests

def send_telegram_notification(success, message, video_title=""):
    """Send Telegram notification on success or failure"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_id:
        print("   ℹ️ إشعارات تليجرام غير مفعلة (مفقود TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID)")
        return
        
    status_icon = "🎉" if success else "❌"
    status_text = "نجاح العملية" if success else "فشل العملية"
    
    text = f"""{status_icon} **تنبيه نشر فيسبوك - {status_text}**

📌 **عنوان الفيديو:** {video_title}
📝 **التفاصيل:** {message}
⏰ **الوقت:** {os.popen('date').read().strip()}
"""
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("   ✅ تم إرسال إشعار تليجرام بنجاح")
        else:
            print(f"   ⚠️ فشل إرسال إشعار تليجرام: {r.text}")
    except Exception as e:
        print(f"   ⚠️ خطأ في إرسال إشعار تليجرام: {e}")

def main():
    print("🚀 Facebook Video Publisher - بدء التشغيل...")
    print(f"   الصفحة: {os.environ.get('FACEBOOK_PAGE_ID', 'غير محدد')}")
    print(f"   Token: {os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN', 'غير محدد')[:10]}...")

    # Step 1: Generate video
    print("\n📝 الخطوة 1-4: توليد الفيديو...")
    try:
        from generateVideo import main as generate_video
        output = asyncio.run(generate_video())
    except Exception as e:
        print(f"❌ فشل توليد الفيديو: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if not output:
        print("❌ فشل توليد الفيديو - لم يتم إرجاع نتيجة")
        sys.exit(1)

    # Step 2: Publish to Facebook
    print("\n📤 الخطوة 5: النشر على فيسبوك...")
    try:
        from publishFacebook import publish_video_to_facebook
        success = publish_video_to_facebook()
    except Exception as e:
        print(f"❌ فشل النشر: {e}")
        import traceback
        traceback.print_exc()
        success = False

    video_title = output.get('title', 'فيديو جديد') if output else 'غير محدد'
    
    if success:
        print("\n🎉 تم توليد ونشر الفيديو بنجاح!")
        send_telegram_notification(True, "تم توليد الفيديو ونشره بنجاح على الصفحة!", video_title)
        sys.exit(0)
    else:
        print("\n⚠️ تم توليد الفيديو بنجاح، لكن النشر التلقائي على فيسبوك فشل.")
        print("   السبب الأرجح: يتطلب Meta Business Verification لصلاحية pages_manage_posts.")
        if output and 'video_path' in output:
            print(f"   ✅ الفيديو محفوظ ويمكنك رفعه يدوياً من: {output['video_path']}")
        print("   💾 هيتم حفظ الفيديو كـ Artifact في هذا الـ run لتحميله ونشره يدوياً.")
        send_telegram_notification(False, "فشل النشر التلقائي على فيسبوك، تم حفظ الفيديو كـ Artifact للرفع اليدوي.", video_title)
        sys.exit(0)


if __name__ == "__main__":
    main()

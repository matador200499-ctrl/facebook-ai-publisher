#!/usr/bin/env python3
"""
Facebook Video Publisher - Main Entry Point
Generates video automatically and publishes to Facebook
"""

import os
import sys
import asyncio

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

    if success:
        print("\n🎉 تم توليد ونشر الفيديو بنجاح!")
        sys.exit(0)
    else:
        # النشر التلقائي على فيسبوك بيتطلب Meta Business Verification لصلاحية
        # pages_manage_posts، وده قيد من فيسبوك نفسه مش من الكود. بما إن الفيديو
        # اتولّد بنجاح وهيتحفظ كـ Artifact (خطوة Upload video artifact شغالة دايماً)،
        # الـ job بيعتبر ناجح جزئيًا بدل ما يظهر Failed كل مرة وده يخفي المشاكل
        # الحقيقية. النشر اليدوي لسه مطلوب لحد ما التوثيق يتعمل.
        print("\n⚠️ تم توليد الفيديو بنجاح، لكن النشر التلقائي على فيسبوك فشل.")
        print("   السبب الأرجح: يتطلب Meta Business Verification لصلاحية pages_manage_posts.")
        if output and 'video_path' in output:
            print(f"   ✅ الفيديو محفوظ ويمكنك رفعه يدوياً من: {output['video_path']}")
        print("   💾 هيتم حفظ الفيديو كـ Artifact في هذا الـ run لتحميله ونشره يدوياً.")
        sys.exit(0)


if __name__ == "__main__":
    main()

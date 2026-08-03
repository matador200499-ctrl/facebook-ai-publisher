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
        print("\n⚠️ تم توليد الفيديو لكن فشل النشر على فيسبوك.")
        if output and 'video_path' in output:
            print(f"   يمكنك رفع الفيديو يدوياً من: {output['video_path']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

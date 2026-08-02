#!/usr/bin/env python3
"""
Facebook Video Publisher - Main Entry Point
Tolida video automatically and publishes to Facebook
"""

import os
import sys
import asyncio

def main():
    print("🚀 Facebook Video Publisher - بدء التشغيل...")
    print(f"   الصفحة: {os.environ.get('FACEBOOK_PAGE_ID', 'غير محدد')}")

    # Step 1: Generate video
    from generateVideo import main as generate_video
    output = asyncio.run(generate_video())

    if not output:
        print("❌ فشل توليد الفيديو")
        sys.exit(1)

    # Step 2: Publish to Facebook
    print("\n📤 الخطوة 5: النشر على فيسبوك...")
    from publishFacebook import publish_video_to_facebook
    success = publish_video_to_facebook()

    if success:
        print("\n🎉 تم توليد ونشر الفيديو بنجاح!")
    else:
        print("\n⚠️ تم توليد الفيديو لكن فشل النشر على فيسبوك.")
        print("   يمكنك رفع الفيديو يدوياً من:")
        print(f"   {output['video_path']}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

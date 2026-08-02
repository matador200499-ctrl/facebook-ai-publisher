#!/usr/bin/env python3
"""
Facebook Video Publisher - Upload Video to Facebook Page
Uses Facebook Graph API to upload video and post text
"""

import os
import sys
import json
import requests
import time

# ─── Configuration ───────────────────────────────────────────────────────────

PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def publish_video_to_facebook():
    """Upload video to Facebook and publish it"""
    # Load generated content
    output_path = os.path.join(OUTPUT_DIR, "output.json")
    if not os.path.exists(output_path):
        print("❌ ملف الإخراج غير موجود. قم بتوليد الفيديو أولاً.")
        sys.exit(1)

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    video_path = data["video_path"]
    post_text = data["post_text"]

    if not os.path.exists(video_path):
        print(f"❌ ملف الفيديو غير موجود: {video_path}")
        sys.exit(1)

    print(f"📤 جاري رفع الفيديو إلى فيسبوك...")
    print(f"   العنوان: {data['title']}")
    print(f"   حجم الملف: {os.path.getsize(video_path) / (1024*1024):.1f} MB")

    # Step 1: Initialize upload
    upload_url = f"https://graph-video.facebook.com/v19.0/{PAGE_ID}/video"

    # Upload video with description
    files = {
        "video_file": open(video_path, "rb")
    }

    params = {
        "access_token": ACCESS_TOKEN,
        "description": post_text,
        "published": "true",
        "content_category": "INSPIRATIONAL",
        "title": data["title"][:50]  # Facebook title limit
    }

    try:
        response = requests.post(upload_url, data=params, files=files, timeout=120)
        result = response.json()

        if "id" in result:
            print(f"\n✅ تم نشر الفيديو بنجاح!")
            print(f"   Video ID: {result['id']}")
            print(f"   الرابط: https://facebook.com/{result['id']}")
            return True
        elif "error" in result:
            error = result["error"]
            print(f"\n❌ خطأ في فيسبوك:")
            print(f"   الرسالة: {error.get('message', 'غير معروف')}")
            print(f"   النوع: {error.get('type', 'غير معروف')}")
            print(f"   الكود: {error.get('code', 'غير معروف')}")

            # Specific error handling
            if error.get("code") == 190:
                print("\n💡 الحل: Token الفيسبوك منتهي الصلاحية!")
                print("   اذهب إلى https://developers.facebook.com/tools/explorer/")
                print("   واحصل على Token جديد وصلاحياته pages_manage_posts")
            elif error.get("code") == 200:
                print("\n💡 الحل: الـ Token لا يملك صلاحيات كافية!")
                print("   تأكد من صلاحيات: pages_manage_posts, pages_show_list")
            return False
        else:
            print(f"\n❌ استجابة غير متوقعة:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return False

    except requests.exceptions.Timeout:
        print("\n❌ انتهى الوقت! الفيديو كبير جداً.")
        print("💡 جرب تقليص مدة الفيديو أو جودته.")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ خطأ في الاتصال بشبكة فيسبوك.")
        return False
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        return False
    finally:
        if "video_file" in files:
            files["video_file"].close()


if __name__ == "__main__":
    success = publish_video_to_facebook()
    sys.exit(0 if success else 1)

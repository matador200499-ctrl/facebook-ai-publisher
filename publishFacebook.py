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
import traceback

# ─── Configuration ───────────────────────────────────────────────────────────

PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def get_token():
    """Get the current access token"""
    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    if not token or len(token) < 10:
        print("   ❌ ERROR: FACEBOOK_PAGE_ACCESS_TOKEN is empty or invalid!")
        print("   Go to GitHub Settings > Secrets > Actions and set FACEBOOK_PAGE_ACCESS_TOKEN")
        return None
    return token


def get_page_token(user_token, page_id):
    """Get page access token from user token by querying the page directly"""
    url = f"https://graph.facebook.com/v21.0/{page_id}"
    params = {
        "access_token": user_token,
        "fields": "access_token,name,id"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if "access_token" in data:
            print(f"   ✅ Got Page Token for: {data.get('name', page_id)}")
            return data["access_token"]
        elif "error" in data:
            err = data["error"]
            print(f"   ⚠️ Error getting page token: {err.get('message', '')}")
    except Exception as e:
        print(f"   ⚠️ Exception: {e}")
    return None


def upload_video(video_path, post_text, title, token):
    """Upload video to Facebook"""
    print(f"\n📤 جاري رفع الفيديو إلى فيسبوك...")
    print(f"   Page ID: {PAGE_ID}")
    print(f"   العنوان: {title}")
    
    file_size = os.path.getsize(video_path)
    print(f"   حجم الملف: {file_size / (1024*1024):.1f} MB")
    
    upload_url = f"https://graph-video.facebook.com/v21.0/{PAGE_ID}/videos"
    print(f"\n🔗 Endpoint: {upload_url}")
    
    try:
        with open(video_path, "rb") as video_file:
            files = {"source": video_file}
            # Enhance description for Social SEO 2026
            seo_description = f"{title}\n\n{post_text}\n\n#bobo_yasoo #AI_Content #SocialSEO"
            
            data = {
                "description": seo_description,
                "title": title, # Adding explicit title for Facebook Video SEO
                "published": "true",
            }
            
            response = requests.post(
                upload_url,
                data=data,
                files=files,
                params={"access_token": token},
                timeout=600
            )
            result = response.json()
            
            if "id" in result:
                print(f"\n✅ تم نشر الفيديو بنجاح!")
                print(f"   Video ID: {result['id']}")
                print(f"   الرابط: https://facebook.com/watch/?v={result['id']}")
                return True
            elif "error" in result:
                error = result["error"]
                code = error.get("code", 0)
                message = error.get("message", "غير معروف")
                err_type = error.get("type", "")
                print(f"\n❌ خطأ (Code: {code}, Type: {err_type}): {message}")
                
                if code == 190:
                    print("\n💡 Token غير صالح! قم بتحديثه:")
                    print("   1. اذهب إلى GitHub Settings > Secrets > Actions")
                    print("   2. حدّث FACEBOOK_PAGE_ACCESS_TOKEN")
                elif code == 100:
                    print(f"\n💡 خطأ في الصفحة (Page ID: {PAGE_ID})")
                    print("   تأكد من صحة Page ID في Secrets")
                elif code == 200:
                    print(f"\n💡 صلاحيات غير كافية: {error.get('message')}")
                elif code == 1:
                    print(f"\n💡 خطأ في API: {message}")
                    print("   حاول مرة أخرى")
                return False
            else:
                print(f"\n❌ استجابة غير متوقعة: {json.dumps(result, indent=2)[:500]}")
                return False
    except Exception as e:
        print(f"\n❌ خطأ في الاتصال: {e}")
        traceback.print_exc()
        return False


def publish_video_to_facebook():
    """Main function to publish video"""
    try:
        # Load generated content
        output_path = os.path.join(OUTPUT_DIR, "output.json")
        if not os.path.exists(output_path):
            print("❌ ملف الإخراج غير موجود. قم بتوليد الفيديو أولاً.")
            print(f"   المسار المتوقع: {output_path}")
            return False

        print("=" * 60)
        print("🎬 Facebook Video Publisher - نشر الفيديو")
        print("=" * 60)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        video_path = data["video_path"]
        post_text = data["post_text"]
        title = data.get("title", "فيديو جديد")

        print(f"\n📋 معلومات الفيديو:")
        print(f"   العنوان: {title}")
        print(f"   المسار: {video_path}")

        if not os.path.exists(video_path):
            print(f"❌ ملف الفيديو غير موجود: {video_path}")
            return False

        # Get token
        print("\n🔑 جاري التحقق من Token...")
        token = get_token()
        if token is None:
            return False
        
        print(f"   Token: {token[:8]}...{token[-8:]}")
        print(f"   Page ID: {PAGE_ID}")

        # If user token, try to get page token
        if token.startswith("EAAT"):
            print("\n🔄 Token من نوع User - جاري الحصول على Page Token...")
            page_token = get_page_token(token, PAGE_ID)
            if page_token:
                token = page_token
                print(f"   ✅ تم الحصول على Page Token")
            else:
                print("   ⚠️ لم نتمكن من الحصول على Page Token - نستخدم User Token")

        # Upload
        success = upload_video(video_path, post_text, title, token)
        
        if not success:
            print(f"\n⚠️ تم توليد الفيديو لكن فشل النشر.")
            print(f"   يمكنك رفع الفيديو يدوياً من: {video_path}")
        
        return success

    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = publish_video_to_facebook()
    sys.exit(0 if success else 1)

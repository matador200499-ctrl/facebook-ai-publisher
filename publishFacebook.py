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

# App credentials for token exchange
APP_ID = os.environ.get("FACEBOOK_APP_ID", "")
APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET", "")


def exchange_to_long_lived_token():
    """Exchange short-lived token for long-lived token (60 days)"""
    if not APP_ID or not APP_SECRET:
        return ACCESS_TOKEN
    
    url = "https://graph.facebook.com/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": ACCESS_TOKEN
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if "access_token" in data:
            print(f"   ✅ تم تحويل Token إلى طويل الأمد ({data.get('expires_in', 'غير محدد')} ثانية)")
            return data["access_token"]
    except Exception:
        pass
    return ACCESS_TOKEN


def get_page_token(user_token, page_id):
    """Get page access token from user token"""
    url = f"https://graph.facebook.com/v21.0/{page_id}"
    params = {
        "access_token": user_token,
        "fields": "access_token,name,id"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if "access_token" in data:
            print(f"   ✅ تم الحصول على Page Token للصفحة: {data.get('name', page_id)}")
            return data["access_token"]
    except Exception:
        pass
    return None


def check_token_info():
    """Check if the token is valid"""
    url = "https://graph.facebook.com/debug_token"
    params = {
        "input_token": ACCESS_TOKEN,
        "access_token": ACCESS_TOKEN
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if "data" in data:
            info = data["data"]
            print(f"   Token type: {info.get('type', 'unknown')}")
            print(f"   Valid: {info.get('is_valid', 'unknown')}")
            print(f"   Expires: {info.get('expires_at', 'unknown')}")
            scopes = info.get('scopes', [])
            print(f"   Scopes: {scopes}")
            return info.get('is_valid', False)
    except Exception as e:
        print(f"   ⚠️ لا يمكن التحقق: {e}")
    return None


def upload_video(video_path, post_text, title):
    """Upload video to Facebook using graph-video API"""
    print(f"\n📤 جاري رفع الفيديو إلى فيسبوك...")
    print(f"   Page ID: {PAGE_ID}")
    print(f"   العنوان: {title}")
    print(f"   حجم الملف: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
    
    # Try both endpoints
    endpoints = [
        f"https://graph-video.facebook.com/v21.0/{PAGE_ID}/videos",
        f"https://graph-video.facebook.com/{PAGE_ID}/videos",
    ]
    
    for upload_url in endpoints:
        print(f"\n🔗 محاولة الاتصال بـ: {upload_url}")
        
        with open(video_path, "rb") as video_file:
            files = {"source": video_file}
            data = {
                "description": post_text,
                "published": "true",
            }
            
            try:
                response = requests.post(
                    upload_url,
                    data=data,
                    files=files,
                    params={"access_token": ACCESS_TOKEN},
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
                    print(f"\n❌ خطأ (Code: {code}): {message}")
                    
                    # Only try next endpoint for connection errors, not auth errors
                    if code == 190:
                        print("   Token غير صالح - لا جدوى من المحاولة مرة أخرى")
                        return False
                    elif code == 100:
                        print("   خطأ في الصفحة - لا جدوى من المحاولة مرة أخرى")
                        return False
                    continue
            except Exception as e:
                print(f"   ⚠️ خطأ في الاتصال: {e}")
                continue
    
    print("\n❌ فشل رفع الفيديو بعد كل المحاولات")
    return False


def publish_video_to_facebook():
    """Main function to publish video"""
    # Load generated content
    output_path = os.path.join(OUTPUT_DIR, "output.json")
    if not os.path.exists(output_path):
        print("❌ ملف الإخراج غير موجود. قم بتوليد الفيديو أولاً.")
        sys.exit(1)

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    video_path = data["video_path"]
    post_text = data["post_text"]
    title = data.get("title", "فيديو جديد")

    if not os.path.exists(video_path):
        print(f"❌ ملف الفيديو غير موجود: {video_path}")
        sys.exit(1)

    print("=" * 60)
    print("🎬 Facebook Video Publisher - نشر الفيديو")
    print("=" * 60)

    # Step 1: Check if we have a user token and need to get page token
    if ACCESS_TOKEN.startswith("EAAT"):
        print("\n🔑 Token من نوع User - جاري الحصول على Page Token...")
        # Try to get page token
        page_token = get_page_token(ACCESS_TOKEN, PAGE_ID)
        if page_token:
            ACCESS_TOKEN = page_token
            # Update the global
            os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"] = ACCESS_TOKEN
        else:
            print("   ⚠️ لم نتمكن من الحصول على Page Token - نحاول بالـ User Token")
    
    # Step 2: Check token validity
    print("\n🔍 التحقق من Token...")
    check_token_info()
    
    # Step 3: Try to exchange for long-lived token
    print("\n🔄 محاولة تحويل Token إلى طويل الأمد...")
    long_lived = exchange_to_long_lived_token()
    if long_lived != ACCESS_TOKEN:
        ACCESS_TOKEN = long_lived
        os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"] = ACCESS_TOKEN

    # Step 4: Verify page access
    print("\n📋 التحقق من الوصول للصفحة...")
    try:
        page_url = f"https://graph.facebook.com/{PAGE_ID}"
        params = {"access_token": ACCESS_TOKEN, "fields": "name,id"}
        r = requests.get(page_url, params=params, timeout=30)
        page_data = r.json()
        if "name" in page_data:
            print(f"   ✅ الصفحة: {page_data['name']} (ID: {page_data['id']})")
        elif "error" in page_data:
            error = page_data["error"]
            print(f"   ❌ خطأ في الوصول: {error.get('message')}")
            print(f"   💡 تأكد أن Token يحتوي على صلاحيات: pages_manage_posts")
            return False
    except Exception as e:
        print(f"   ⚠️ خطأ: {e}")

    # Step 5: Upload video
    success = upload_video(video_path, post_text, title)
    
    if not success:
        print(f"\n⚠️ تم توليد الفيديو لكن فشل النشر.")
        print(f"   يمكنك رفع الفيديو يدوياً من: {video_path}")
    
    return success


if __name__ == "__main__":
    success = publish_video_to_facebook()
    sys.exit(0 if success else 1)

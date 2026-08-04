#!/usr/bin/env python3
"""
Facebook Video Publisher - Generate Video from AI Script
Pipeline: Gemini AI (REST) → Script → edge-tts Audio → Pollinations Images → FFmpeg Video
"""

import os
import sys
import json
import subprocess
import asyncio
import edge_tts
import requests
import tempfile
import re
import time

# ─── Configuration ───────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VOICE = "ar-EG-SalmaNeural"  # Female Egyptian Arabic voice
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")

# Pollinations.ai topics for images
IMAGE_THEMES = [
    "motivation success",
    "inspirational sunrise",
    "knowledge books",
    "ancient wisdom",
    "technology future",
    "nature peace",
    "space stars",
    "desert wisdom",
    "education learning",
    "leadership power",
]

# ─── Step 1: Generate Script with Gemini AI (REST API) ──────────────────────

def generate_script(topic=None):
    """Generate a video script using Gemini AI via REST API"""
    if topic is None:
        topics = [
            "حكمة يومية تحفيزية",
            "درس من التاريخ الإسلامي",
            "نصيحة في علم النفس",
            "اكتشاف علمي مدهش",
            "قصة نجاح ملهمة",
            "معلومة لا يعرفها كثيرون",
            "نصيحة للتطوير الذاتي",
            "عظمة الخالق في الطبيعة",
        ]
        topic = topics[int(time.time()) % len(topics)]

    prompt = f"""أنت كاتب سكربتات فيديو احترافي. اكتب سكربت فيديو قصير (دقيقة واحدة) باللغة العربية الفصحى عن الموضوع التالي:

الموضوع: {topic}

المطلوب:
1. عنوان جذاب للفيديو (10 كلمات كحد أقصى)
2. مقدمة قوية تشد الانتباه (جملة واحدة)
3. 4-5 جمل محتوى قيمة ومفيدة
4. خاتمة تحفيزية (جملة واحدة)
5. هاشتاجات مناسبة (3 هاشتاجات)

أجب بهذا التنسيق بالضبط:
عنوان: [العنوان]
مقدمة: [المقدمة]
جمل:
- [جملة 1]
- [جملة 2]
- [جملة 3]
- [جملة 4]
- [جملة 5]
خاتمة: [الخاتمة]
هاشتاجات: [هاشتاج1] [هاشتاج2] [هاشتاج3]

ملاحظة: اكتب بجمل بسيطة وقوية ومناسبة للنطق الصوتي. لا تستخدم رموز أو أرقام معقدة."""

    # Try multiple Gemini models
    models = [
        "gemini-1.5-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash",
    ]

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 1000
            }
        }

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"   ✅ تم استخدام نموذج: {model}")
                script = parse_script(text)
                if script["title"]:
                    return script
                print(f"   ⚠️ النموذج {model} لم يرجع عنوان - نجرب التالي")
            elif response.status_code == 429 or response.status_code == 503:
                print(f"   ⚠️ {model}: غير متاح حالياً ({response.status_code})")
                time.sleep(2)
                continue
            elif response.status_code == 404:
                print(f"   ⚠️ {model}: غير متوفر")
                continue
            else:
                print(f"   ⚠️ {model}: خطأ {response.status_code}")
                continue
        except Exception as e:
            print(f"   ⚠️ {model}: خطأ {e}")
            continue

    # Fallback to default script
    print("   ⚠️ جاري استخدام سكربت احتياطي...")
    return parse_script(_get_fallback_script())


def _get_fallback_script():
    """Fallback script when Gemini fails"""
    return """عنوان: سر النجاح الحقيقي
مقدمة: هل تساءلت يوماً لماذا ينجح بعض الناس بينما يفشل الاخرون؟
جمل:
- النجاح ليس حظاً بل هو نتيجة عمل مستمر وتخطيط ذكي
- كل شخص ناجح واجه صعوبات كثيرة لكنه لم يستسلم ابداً
- الثقة بالنفس هي المفتاح الاول لتحقيق اي هدف
- التعلم المستمر والتطوير الذاتي هما سلاحك الاقوى
- لا تقارن نفسك بالاخرين بل قارن نفسك بامستقبلك
خاتمة: ابدا اليوم واتخذ خطوة واحدة نحو حلمك.
هاشتاجات: #تحفيز #نجاح #تطوير_الذات"""


def parse_script(text):
    """Parse the Gemini response into structured script"""
    script = {
        "title": "",
        "intro": "",
        "sentences": [],
        "conclusion": "",
        "hashtags": ""
    }

    # Extract title
    title_match = re.search(r'عنوان[:\uff1a]\s*(.+)', text)
    if title_match:
        script["title"] = title_match.group(1).strip()

    # Extract intro
    intro_match = re.search(r'مقدمة[:\uff1a]\s*(.+)', text)
    if intro_match:
        script["intro"] = intro_match.group(1).strip()

    # Extract sentences
    sentences = re.findall(r'-\s*(.+)', text)
    script["sentences"] = [s.strip() for s in sentences if s.strip()]

    # Extract conclusion
    conclusion_match = re.search(r'خاتمة[:\uff1a]\s*(.+)', text)
    if conclusion_match:
        script["conclusion"] = conclusion_match.group(1).strip()

    # Extract hashtags
    hashtag_match = re.search(r'هاشتاجات[:\uff1a]\s*(.+)', text)
    if hashtag_match:
        script["hashtags"] = hashtag_match.group(1).strip()

    return script


# ─── Step 2: Generate Audio with edge-tts ────────────────────────────────────

async def generate_audio(text, output_path):
    """Generate Arabic audio using edge-tts (Microsoft free TTS)"""
    communicate = edge_tts.Communicate(text, VOICE, rate="-10%")
    submaker = edge_tts.SubMaker()

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    srt_content = submaker.get_srt()
    # Save SRT to temp
    srt_path = os.path.join(TEMP_DIR, "audio_subs.srt")
    with open(srt_path, "w", encoding="utf-8") as sf:
        sf.write(srt_content)
    return srt_content


def get_full_script_text(script):
    """Combine all script parts into full narration text"""
    parts = []
    if script.get("intro"):
        parts.append(script["intro"])
    for sentence in script.get("sentences", []):
        parts.append(sentence)
    if script.get("conclusion"):
        parts.append(script["conclusion"])
    return " ".join(parts)


# ─── Step 3: Generate Images with Pollinations.ai (with retry + local fallback) ──

# Minimum size (bytes) for a downloaded file to be considered a valid image.
# Pollinations sometimes returns a tiny error payload with a 200 status too,
# so we check both the HTTP status AND the actual file size.
MIN_VALID_IMAGE_BYTES = 5000

# Alternate image sources / seeds to retry with, in order.
POLLINATIONS_MODELS = ["flux", "turbo"]  # pollinations model param, if available


def _download_pollinations_image(prompt, output_path, width, height, seed, model=None):
    """Single attempt to download one image from Pollinations.ai.
    Returns True only if the request succeeded AND the file looks like a real image."""
    encoded_prompt = requests.utils.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&nologo=true&seed={seed}"
    )
    if model:
        url += f"&model={model}"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        if len(response.content) < MIN_VALID_IMAGE_BYTES:
            print(f"   ⚠️ الصورة صغيرة جداً/فاسدة ({len(response.content)} بايت) - نعتبرها فشل")
            return False
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"   ⚠️ فشل تحميل الصورة: {e}")
        return False


def _download_picsum_image(output_path, width, height):
    """Second-tier fallback: fetch a random real photo from Lorem Picsum.
    No API key needed, doesn't depend on prompt matching, but is far more
    visually usable than a flat placeholder if Pollinations is completely down."""
    seed = int(time.time() * 1000) % 1000000
    url = f"https://picsum.photos/seed/{seed}/{width}/{height}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if len(response.content) < MIN_VALID_IMAGE_BYTES:
            return False
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"   🖼️ استُخدمت صورة احتياطية من Picsum بدلاً من Pollinations")
        return True
    except Exception as e:
        print(f"   ⚠️ فشل تحميل الصورة الاحتياطية من Picsum: {e}")
        return False


def _make_local_placeholder_image(output_path, text, width=1280, height=720):
    """Last-resort fallback: generate a simple solid-color placeholder image locally
    using Pillow, so the pipeline can still produce a video even if Pollinations
    AND Picsum are both down. Requires Pillow (pip install Pillow)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import random

        colors = [(30, 30, 60), (20, 50, 70), (50, 30, 60), (25, 45, 35), (55, 40, 20)]
        bg = random.choice(colors)
        img = Image.new("RGB", (width, height), color=bg)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
            )
        except Exception:
            font = ImageFont.load_default()

        # Simple centered watermark-style text so scenes aren't just blank
        label = text[:20] if text else "..."
        try:
            bbox = draw.textbbox((0, 0), label, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = (len(label) * 20, 40)
        draw.text(((width - tw) / 2, (height - th) / 2), label, fill=(230, 230, 230), font=font)

        img.save(output_path, "JPEG", quality=85)
        return True
    except Exception as e:
        print(f"   ❌ فشل حتى إنشاء صورة احتياطية محلية: {e}")
        return False


def generate_image(prompt, output_path, width=1280, height=720, max_retries=3):
    """Generate an image using Pollinations.ai (free, no API key needed),
    with retries and a random seed each attempt so a repeated 500 doesn't
    hit the exact same broken request."""
    for attempt in range(1, max_retries + 1):
        seed = int(time.time() * 1000) % 1000000 + attempt
        ok = _download_pollinations_image(prompt, output_path, width, height, seed)
        if ok:
            print(f"✅ Image saved: {output_path} (attempt {attempt})")
            return True
        if attempt < max_retries:
            wait = attempt * 3
            print(f"   ⏳ إعادة محاولة توليد الصورة خلال {wait} ثانية... (محاولة {attempt + 1}/{max_retries})")
            time.sleep(wait)

    print(f"❌ فشلت كل محاولات Pollinations لهذه الصورة، هنجرب مصدر بديل (Picsum)")
    if _download_picsum_image(output_path, width, height):
        return True

    print(f"   ❌ فشل Picsum أيضاً، هنستخدم صورة احتياطية محلية كملاذ أخير")
    return _make_local_placeholder_image(output_path, prompt)


def generate_scene_images(script, num_scenes=5):
    """Generate images for each scene of the video.
    Tries Kaggle GPU (Stable Diffusion, higher quality + more reliable) first
    if configured; falls back to the Pollinations -> Picsum -> local
    placeholder chain per-scene for anything Kaggle didn't produce.
    Only paths that actually exist on disk are returned, so downstream
    FFmpeg never receives a missing file."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    images = [None] * num_scenes

    # Get a random theme
    theme = IMAGE_THEMES[int(time.time()) % len(IMAGE_THEMES)]

    prompts = []
    for i in range(num_scenes):
        prompt_options = [
            f"{theme}, beautiful artistic, cinematic lighting, high quality",
            f"abstract art, {theme}, inspirational, warm colors",
            f"epic landscape, {theme}, dramatic lighting, 4k quality",
            f"artistic illustration, {theme}, professional design",
            f"creative visual, {theme}, modern digital art",
        ]
        prompts.append(prompt_options[i % len(prompt_options)])

    try:
        from kaggle_client import generate_images_via_kaggle
        kaggle_images = generate_images_via_kaggle(prompts, TEMP_DIR)
    except Exception as e:
        print(f"⚠️ تخطي Kaggle بسبب خطأ غير متوقع: {e}")
        kaggle_images = None

    if kaggle_images:
        for i, path in enumerate(kaggle_images):
            if i < num_scenes:
                images[i] = path
        print(f"✅ Kaggle ولّد {len(kaggle_images)}/{num_scenes} صورة")

    for i in range(num_scenes):
        if images[i] is not None:
            continue
        image_path = os.path.join(TEMP_DIR, f"scene_{i:02d}.jpg")
        success = generate_image(prompts[i], image_path)
        if success and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
            images[i] = image_path
        else:
            print(f"   ⚠️ تخطي المشهد {i} - لا توجد صورة صالحة")

    images = [p for p in images if p is not None]

    if not images:
        raise RuntimeError(
            "فشل توليد كل الصور (Kaggle + Pollinations + الاحتياطي المحلي)، "
            "لا يمكن إنشاء فيديو بدون صور. تحقق من اتصال الشبكة أو من تثبيت مكتبة Pillow."
        )

    return images


# ─── Step 4: Create Video with FFmpeg ────────────────────────────────────────

def create_video(images, audio_path, script, output_path):
    """Create video from images + audio using FFmpeg"""
    num_images = len(images)
    if num_images == 0:
        return False

    # Get audio duration
    duration_result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    audio_duration = float(duration_result.stdout.strip())

    # Simple approach: single image slideshow
    if num_images == 1:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", images[0],
            "-i", audio_path,
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(audio_duration),
            "-pix_fmt", "yuv420p",
            output_path
        ]
    else:
        # Create clips for each image
        duration_per_image = audio_duration / num_images
        clips = []

        for i, img in enumerate(images):
            clip_path = os.path.join(TEMP_DIR, f"clip_{i:02d}.mp4")
            cmd_clip = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", img,
                "-vf", f"scale=1280:720,format=yuv420p",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-t", str(duration_per_image),
                "-pix_fmt", "yuv420p",
                clip_path
            ]
            result = subprocess.run(cmd_clip, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                clips.append(clip_path)
            else:
                print(f"   ⚠️ فشل بناء clip للصورة {img}: {result.stderr[-300:]}")

        if not clips:
            print("❌ لم ينجح بناء أي clip من الصور")
            return False

        # Concat clips with audio
        concat_path = os.path.join(TEMP_DIR, "concat_list.txt")
        with open(concat_path, "w") as f:
            for clip in clips:
                f.write(f"file '{clip}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ Video created: {output_path}")
            print(f"   Size: {os.path.getsize(output_path) / (1024*1024):.1f} MB")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr[-500:]}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ─── Step 5: Generate Facebook Post Text ─────────────────────────────────────

def generate_facebook_post(script):
    """Generate the Facebook post text"""
    title = script.get("title", "فيديو تحفيزي")
    hashtags = script.get("hashtags", "#تحفيز #تطوير_الذات #نجاح")

    post_text = f"📹 {title}\n\n"
    if script.get("intro"):
        post_text += f"{script['intro']}\n\n"
    if script.get("sentences"):
        for s in script["sentences"][:3]:
            post_text += f"✨ {s}\n"
        post_text += "\n"
    if script.get("conclusion"):
        post_text += f"{script['conclusion']}\n\n"
    post_text += f"\n{hashtags}\n"

    return post_text


# ─── Main Pipeline ───────────────────────────────────────────────────────────

async def main():
    """Main video generation pipeline"""
    print("=" * 60)
    print("🎬 Facebook Video Publisher - توليد فيديو تلقائي")
    print("=" * 60)

    # Setup
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Step 1: Generate script
    print("\n📝 الخطوة 1: توليد سكربت الفيديو...")
    script = generate_script()
    print(f"   العنوان: {script['title']}")
    print(f"   عدد الجمل: {len(script['sentences'])}")

    # Save script
    script_path = os.path.join(OUTPUT_DIR, "script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    # Step 2: Generate audio
    print("\n🔊 الخطوة 2: توليد الصوت...")
    full_text = get_full_script_text(script)
    audio_path = os.path.join(TEMP_DIR, "narration.mp3")
    await generate_audio(full_text, audio_path)
    print(f"   الملف: {audio_path}")

    # Step 3: Generate images
    print("\n🖼️ الخطوة 3: توليد الصور...")
    num_scenes = max(len(script["sentences"]) + 2, 4)
    try:
        images = generate_scene_images(script, num_scenes)
    except RuntimeError as e:
        print(f"❌ {e}")
        return None
    print(f"   تم توليد {len(images)} صورة صالحة من أصل {num_scenes}")

    # Step 4: Create video
    print("\n🎥 الخطوة 4: إنشاء الفيديو...")
    video_path = os.path.join(OUTPUT_DIR, "video.mp4")
    success = create_video(images, audio_path, script, video_path)

    if not success:
        print("❌ فشل إنشاء الفيديو")
        return None

    # Step 5: Generate post text
    post_text = generate_facebook_post(script)

    # Save all outputs
    output = {
        "video_path": video_path,
        "post_text": post_text,
        "script": script,
        "title": script.get("title", ""),
        "hashtags": script.get("hashtags", "")
    }

    output_json_path = os.path.join(OUTPUT_DIR, "output.json")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("✅ تم إنشاء الفيديو بنجاح!")
    print(f"   الفيديو: {video_path}")
    print(f"   حجم الملف: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
    print("=" * 60)

    return output


if __name__ == "__main__":
    result = asyncio.run(main())

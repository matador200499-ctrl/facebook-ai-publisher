#!/usr/bin/env python3
"""
Facebook Video Publisher - Generate Video from AI Script
Pipeline: Gemini AI → Script → edge-tts Audio → Pollinations Images → FFmpeg Video
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

# ─── Step 1: Generate Script with Gemini AI ──────────────────────────────────

def generate_script(topic=None):
    """Generate a video script using Gemini AI in Arabic"""
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

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

    response = model.generate_content(prompt)
    text = response.text

    # Parse the response
    script = parse_script(text)
    return script

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
    title_match = re.search(r'عنوان[:：]\s*(.+)', text)
    if title_match:
        script["title"] = title_match.group(1).strip()

    # Extract intro
    intro_match = re.search(r'مقدمة[:：]\s*(.+)', text)
    if intro_match:
        script["intro"] = intro_match.group(1).strip()

    # Extract sentences
    sentences = re.findall(r'-\s*(.+)', text)
    script["sentences"] = [s.strip() for s in sentences if s.strip()]

    # Extract conclusion
    conclusion_match = re.search(r'خاتمة[:：]\s*(.+)', text)
    if conclusion_match:
        script["conclusion"] = conclusion_match.group(1).strip()

    # Extract hashtags
    hashtag_match = re.search(r'هاشتاجات[:：]\s*(.+)', text)
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

# ─── Step 3: Generate Images with Pollinations.ai ────────────────────────────

def generate_image(prompt, output_path, width=1280, height=720):
    """Generate an image using Pollinations.ai (free, no API key needed)"""
    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={int(time.time())}"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Image saved: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        return False

def generate_scene_images(script, num_scenes=5):
    """Generate images for each scene of the video"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    images = []

    # Get a random theme
    theme = IMAGE_THEMES[int(time.time()) % len(IMAGE_THEMES)]

    for i in range(num_scenes):
        image_path = os.path.join(TEMP_DIR, f"scene_{i:02d}.jpg")
        # Create descriptive prompt for each scene
        prompts = [
            f"{theme}, beautiful artistic, cinematic lighting, high quality",
            f"abstract art, {theme}, inspirational, warm colors",
            f"epic landscape, {theme}, dramatic lighting, 4k quality",
            f"artistic illustration, {theme}, professional design",
            f"creative visual, {theme}, modern digital art",
        ]
        prompt = prompts[i % len(prompts)]
        generate_image(prompt, image_path)
        images.append(image_path)

    return images

# ─── Step 4: Create Video with FFmpeg ────────────────────────────────────────

def create_video(images, audio_path, script, output_path):
    """Create video from images + audio using FFmpeg"""
    num_images = len(images)
    if num_images == 0:
        return False

    # Calculate duration per image based on audio length
    # First get audio duration
    duration_result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    audio_duration = float(duration_result.stdout.strip())

    # Each image shows for audio_duration / num_images seconds
    duration_per_image = audio_duration / num_images

    # Create input list for FFmpeg concat
    input_list_path = os.path.join(TEMP_DIR, "input_list.txt")
    with open(input_list_path, "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_image}\n")
        # Add last image again (FFmpeg requirement)
        f.write(f"file '{images[-1]}'\n")

    # Create caption file (SRT format)
    srt_path = os.path.join(TEMP_DIR, "captions.srt")
    create_srt_captions(script, audio_duration, srt_path)

    # FFmpeg command: slideshow with audio + subtitles
    # Use fade transitions between images
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", input_list_path,
        "-i", audio_path,
        "-vf", f"scale=1280:720,format=yuv420p,subtitles={srt_path}:force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,MarginV=50'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
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
            # Try simpler command without subtitles
            return create_video_simple(images, audio_path, output_path)
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timed out")
        return False

def create_video_simple(images, audio_path, output_path):
    """Simpler video creation without subtitles if complex version fails"""
    num_images = len(images)

    duration_result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    audio_duration = float(duration_result.stdout.strip())
    duration_per_image = audio_duration / num_images

    # Simple command: loop images with crossfade
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "1/{}".format(int(duration_per_image)),
        "-i", images[0] if num_images == 1 else None,
    ]

    if num_images == 1:
        # Single image for full duration
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
        # Multiple images - create individual clips and concat
        clips = []
        for i, img in enumerate(images):
            clip_path = os.path.join(TEMP_DIR, f"clip_{i:02d}.mp4")
            cmd_clip = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", img,
                "-vf", f"scale=1280:720,format=yuv420p,zoompan=z='min(zoom+0.001,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration_per_image*30)}:s=1280x720:fps=30",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-t", str(duration_per_image),
                "-pix_fmt", "yuv420p",
                clip_path
            ]
            subprocess.run(cmd_clip, capture_output=True, timeout=60)
            clips.append(clip_path)

        # Concat all clips
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
            print(f"✅ Video created (simple): {output_path}")
            print(f"   Size: {os.path.getsize(output_path) / (1024*1024):.1f} MB")
            return True
        else:
            print(f"❌ Error: {result.stderr[-300:]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_srt_captions(script, total_duration, output_path):
    """Create SRT subtitle file"""
    parts = []
    if script.get("intro"):
        parts.append(script["intro"])
    for sentence in script.get("sentences", []):
        parts.append(sentence)
    if script.get("conclusion"):
        parts.append(script["conclusion"])

    total_parts = len(parts)
    duration_per_part = total_duration / total_parts

    with open(output_path, "w", encoding="utf-8") as f:
        for i, part in enumerate(parts):
            start = i * duration_per_part
            end = (i + 1) * duration_per_part
            start_fmt = format_time(start)
            end_fmt = format_time(end)
            f.write(f"{i + 1}\n")
            f.write(f"{start_fmt} --> {end_fmt}\n")
            f.write(f"{part}\n\n")

def format_time(seconds):
    """Format seconds to SRT time format"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ─── Step 5: Generate Facebook Post Text ─────────────────────────────────────

def generate_facebook_post(script):
    """Generate the Facebook post text"""
    title = script.get("title", "فيديو تحفيزي")
    hashtags = script.get("hashtags", "#تحفيز #تطوير_الذات #نجاح")

    post_text = f"📹 {title}\n\n"
    if script.get("intro"):
        post_text += f"{script['intro']}\n\n"
    if script.get("sentences"):
        for s in script["sentences"][:3]:  # Show first 3 sentences
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
    num_scenes = max(len(script["sentences"]) + 2, 4)  # +2 for intro and conclusion
    images = generate_scene_images(script, num_scenes)
    print(f"   تم توليد {len(images)} صورة")

    # Step 4: Create video
    print("\n🎥 الخطوة 4: إنشاء الفيديو...")
    video_path = os.path.join(OUTPUT_DIR, "video.mp4")
    success = create_video(images, audio_path, script, video_path)

    if not success:
        print("❌ فشل إنشاء الفيديو")
        sys.exit(1)

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

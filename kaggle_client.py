"""
Orchestrates image generation on Kaggle's free GPU:
1. Templates the prompt list into kaggle_worker/generate_images.py
2. Pushes it as a Kaggle kernel (`kaggle kernels push`)
3. Polls kernel status until it finishes (or times out)
4. Downloads the generated images

Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables (from GitHub
Secrets). If they're missing, or anything here fails, the caller should fall
back to the existing Pollinations -> Picsum -> local placeholder chain.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time

WORKER_DIR = os.path.join(os.path.dirname(__file__), "kaggle_worker")
POLL_INTERVAL_SECONDS = 20
DEFAULT_TIMEOUT_SECONDS = 600  # 10 minutes: model load + generation + queue time


def _kaggle_available():
    return bool(os.environ.get("KAGGLE_USERNAME")) and bool(os.environ.get("KAGGLE_KEY"))


def _run(cmd, cwd=None, timeout=120):
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", str(e)


def generate_images_via_kaggle(prompts, output_dir, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """Returns a list of local image file paths (one per prompt, in order),
    or None if generation failed / Kaggle isn't configured. Never raises —
    callers should treat None as "fall back to the other image sources"."""

    if not _kaggle_available():
        print("ℹ️ Kaggle غير مُعد (KAGGLE_USERNAME/KAGGLE_KEY غير موجودين)، تخطي")
        return None

    username = os.environ["KAGGLE_USERNAME"]
    kernel_id = f"{username}/fb-ai-publisher-image-gen"

    with tempfile.TemporaryDirectory() as tmp:
        # 1) Template the prompts into the worker script
        with open(os.path.join(WORKER_DIR, "generate_images.py"), "r", encoding="utf-8") as f:
            script = f.read()
        prompts_json = json.dumps(prompts, ensure_ascii=False).replace("'", "\\'")
        script = script.replace("__PROMPTS_JSON__", prompts_json)
        with open(os.path.join(tmp, "generate_images.py"), "w", encoding="utf-8") as f:
            f.write(script)

        with open(os.path.join(WORKER_DIR, "kernel-metadata.json"), "r", encoding="utf-8") as f:
            meta = f.read().replace("__KAGGLE_USERNAME__", username)
        with open(os.path.join(tmp, "kernel-metadata.json"), "w", encoding="utf-8") as f:
            f.write(meta)

        # 2) Push the kernel to Kaggle (starts running immediately)
        print(f"🚀 بعت {len(prompts)} prompt لـ Kaggle GPU ({kernel_id})...")
        code, out, err = _run(["kaggle", "kernels", "push", "-p", tmp], timeout=120)
        if code != 0:
            print(f"❌ فشل رفع الـ kernel لـ Kaggle: {err or out}")
            return None

        # 3) Poll until it's done
        deadline = time.time() + timeout_seconds
        status = None
        while time.time() < deadline:
            time.sleep(POLL_INTERVAL_SECONDS)
            code, out, err = _run(["kaggle", "kernels", "status", kernel_id], timeout=60)
            if code != 0:
                print(f"⚠️ تعذر التحقق من حالة الـ kernel: {err or out}")
                continue
            status = out.strip()
            print(f"   ⏳ حالة Kaggle: {status}")
            if "complete" in status.lower():
                break
            if "error" in status.lower() or "cancel" in status.lower():
                print(f"❌ فشل تشغيل الـ kernel على Kaggle: {status}")
                return None
        else:
            print(f"❌ انتهت المهلة ({timeout_seconds}s) قبل ما Kaggle يخلص")
            return None

        if not status or "complete" not in status.lower():
            return None

        # 4) Download the output images
        os.makedirs(output_dir, exist_ok=True)
        code, out, err = _run(
            ["kaggle", "kernels", "output", kernel_id, "-p", output_dir, "--force"],
            timeout=180,
        )
        if code != 0:
            print(f"❌ فشل تنزيل نتائج Kaggle: {err or out}")
            return None

        image_paths = []
        for i in range(len(prompts)):
            candidate = os.path.join(output_dir, "output", f"scene_{i:02d}.jpg")
            if not os.path.exists(candidate):
                # kaggle kernels output sometimes flattens the directory structure
                candidate = os.path.join(output_dir, f"scene_{i:02d}.jpg")
            if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
                final_path = os.path.join(output_dir, f"kaggle_scene_{i:02d}.jpg")
                shutil.copy(candidate, final_path)
                image_paths.append(final_path)
            else:
                print(f"   ⚠️ الصورة {i} مش موجودة في نتيجة Kaggle")

        if len(image_paths) != len(prompts):
            print(f"⚠️ Kaggle ولّد {len(image_paths)}/{len(prompts)} صورة بس")

        return image_paths if image_paths else None

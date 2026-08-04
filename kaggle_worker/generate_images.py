"""
Kaggle GPU worker: generates one image per prompt using SD-Turbo (fast,
single-step diffusion — ideal for free T4/P100 GPUs and short batch jobs).

This file is a TEMPLATE. The `__PROMPTS_JSON__` marker below gets replaced
with a real JSON list of prompts by kaggle_client.py before the kernel is
pushed to Kaggle. Do not edit the marker format.
"""

import json
import os

import torch
from diffusers import AutoPipelineForText2Image

PROMPTS = json.loads('__PROMPTS_JSON__')

OUTPUT_DIR = "/kaggle/working/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sd-turbo",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
)
pipe = pipe.to(device)

for i, prompt in enumerate(PROMPTS):
    print(f"[{i + 1}/{len(PROMPTS)}] Generating: {prompt}")
    image = pipe(
        prompt=prompt,
        num_inference_steps=1,
        guidance_scale=0.0,
        width=768,
        height=432,
    ).images[0]
    image = image.resize((1280, 720))
    out_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.jpg")
    image.save(out_path, quality=90)
    print(f"   saved -> {out_path}")

print(f"DONE: {len(PROMPTS)} images generated")

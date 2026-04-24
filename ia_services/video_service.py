import os
import time
import torch
from PIL import Image
import cv2
import numpy as np

from diffusers import (
    StableVideoDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline
)

# -------------------------
# 🔥 PIPES GLOBALES
# -------------------------
pipe_video = None
pipe_text2img = None
pipe_img2img = None


# -------------------------
# 🎬 VIDEO (SVD)
# -------------------------
def get_video_pipe():
    global pipe_video

    if pipe_video is None:
        print("🎬 Cargando SVD...")

        pipe_video = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid",
            torch_dtype=torch.float32
        ).to("cpu")

    return pipe_video


# -------------------------
# 🧠 TEXTO → IMAGEN (SDXL)
# -------------------------
def get_text2img_pipe():
    global pipe_text2img

    if pipe_text2img is None:
        print("🧠 Cargando SDXL (text2img)...")

        pipe_text2img = StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float32,
            local_files_only=True
        ).to("cpu")

        pipe_text2img.enable_attention_slicing()

    return pipe_text2img


# -------------------------
# 🖼️ IMAGEN → IMAGEN (SDXL)
# -------------------------
def get_img2img_pipe():
    global pipe_img2img

    if pipe_img2img is None:
        print("🖼️ Cargando SDXL (img2img)...")

        pipe_img2img = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float32,
            local_files_only=True
        ).to("cpu")

        pipe_img2img.enable_attention_slicing()

    return pipe_img2img


# -------------------------
# 🎬 GENERADOR PRINCIPAL
# -------------------------
def generar_video(
    prompt="",
    ruta_imagen=None,
    frames=14,
    fps=7,
    width=768,
    height=432
):

    pipe_video = get_video_pipe()

    frames = min(max(frames, 8), 25)
    fps = min(max(fps, 4), 12)

    # -------------------------
    # 🧠 CASO 1: SOLO PROMPT
    # -------------------------
    if prompt and not ruta_imagen:

        pipe = get_text2img_pipe()

        print("🧠 Generando imagen desde prompt...")

        image = pipe(
            prompt,
            num_inference_steps=30,
            guidance_scale=7.5
        ).images[0]

    # -------------------------
    # 🖼️ CASO 2: SOLO IMAGEN
    # -------------------------
    elif ruta_imagen and not prompt:

        print("🖼️ Usando imagen directa...")

        image = Image.open(ruta_imagen).convert("RGB")

    # -------------------------
    # 🔥 CASO 3: PROMPT + IMAGEN
    # -------------------------
    elif ruta_imagen and prompt:

        pipe = get_img2img_pipe()

        print("🔥 Refinando imagen con prompt...")

        base = Image.open(ruta_imagen).convert("RGB")

        image = pipe(
            prompt=prompt,
            image=base,
            strength=0.35,  # 🔥 mantiene identidad
            num_inference_steps=30,
            guidance_scale=7.5
        ).images[0]

    else:
        raise Exception("❌ Necesitas prompt o imagen")

    # -------------------------
    # 🎬 PREPARAR PARA SVD
    # -------------------------
    width, height = 576, 320
    image = image.resize((width, height))

    print("🎬 Generando vídeo...")

    result = pipe_video(
        image,
        num_frames=frames,
        motion_bucket_id=127,
        noise_aug_strength=0.02
    )

    frames_data = result.frames[0]

    # -------------------------
    # 💾 GUARDAR
    # -------------------------
    if not os.path.exists("files"):
        os.makedirs("files")

    filename = f"video_{int(time.time())}.mp4"
    path = os.path.join("files", filename)

    print("💾 Guardando vídeo...")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(path, fourcc, fps, (width, height))

    if not video.isOpened():
        raise Exception("❌ Error creando vídeo")

    for frame in frames_data:
        frame_np = np.array(frame)
        frame_np = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        video.write(frame_np)

    video.release()

    return filename


# compatibilidad
def generar_video_pro(**kwargs):
    return generar_video(**kwargs)
from diffusers import StableDiffusionPipeline
import torch

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5"
)

pipe = pipe.to("cpu")  # en Mac sin GPU

prompt = "modern kitchen renovation, realistic, high quality"

image = pipe(prompt).images[0]

image.save("test.png")

print("Imagen generada")
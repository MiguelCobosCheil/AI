from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch

# 🔥 carga global
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 🔥 etiquetas REALISTAS (MUCHO MEJOR)
LABELS = [
    "a photo of a building",
    "a photo of a palace",
    "a photo of a monument",
    "a photo of a city",
    "a photo of a landscape",
    "a photo of a person",
    "a photo of a group of people",
    "a screenshot of a website",
    "a screenshot of an email",
    "a photo of a document",
    "an invoice document",
    "a contract document",
    "a table of data",
    "a bar chart",
    "a line chart",
    "a pie chart",
    "a logo",
    "a product",
    "a mobile app screen"
]


def limpiar_label(label):
    """
    Limpia etiquetas tipo:
    'a photo of a palace' → 'palace'
    """
    return (
        label.replace("a photo of ", "")
        .replace("a screenshot of ", "")
        .replace("an ", "")
        .replace("a ", "")
        .strip()
    )


def analizar_imagen_clip(ruta_imagen):
    try:
        image = Image.open(ruta_imagen).convert("RGB")

        inputs = processor(
            text=LABELS,
            images=image,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():
            outputs = model(**inputs)

        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)

        best_idx = probs.argmax().item()
        raw_label = LABELS[best_idx]
        confidence = probs[0][best_idx].item()

        label = limpiar_label(raw_label)

        return {
            "label": label,
            "confidence": round(confidence, 3)
        }

    except Exception as e:
        return {
            "label": "unknown",
            "confidence": 0,
            "error": str(e)
        }
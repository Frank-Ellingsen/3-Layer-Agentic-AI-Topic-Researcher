import os
import re
import urllib.parse
import requests
import config

def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[\s-]+', '_', clean)

def generate_topic_header_image(topic: str) -> str:
    """
    Generates a high-quality 16:9 executive presentation header image 
    tailored specifically to the given topic and saves it in outputs/assets/.
    Returns the path to the saved header image file.
    """
    assets_dir = os.path.join("outputs", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    filename = f"{sanitize_filename(topic)}_header.jpg"
    target_path = os.path.join(assets_dir, filename)
    
    # If image already exists for this topic, return it
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
        return target_path

    # Prompt engineered specifically for the topic
    prompt = (
        f"Executive presentation header banner for {topic}, "
        f"professional corporate aesthetic, sleek modern design, muted slate and dark blue tones, "
        f"16:9 widescreen layout, high-resolution cinematic visual"
    )

    # 1. Try Gemini Imagen API if key available and quota allows
    if config.GEMINI_API_KEY:
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from google import genai
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                res = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=prompt,
                    config=dict(number_of_images=1, aspect_ratio="16:9")
                )
                if res.generated_images:
                    with open(target_path, "wb") as f:
                        f.write(res.generated_images[0].image.image_bytes)
                    print(f"[ImageGenerator] Generated header image via Gemini Imagen for '{topic}'")
                    return target_path
        except Exception:
            pass

    # 2. Try Pollinations AI image generator
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&seed={abs(hash(topic)) % 10000}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(target_path, "wb") as f:
                f.write(resp.content)
            print(f"[ImageGenerator] Generated header image via Pollinations AI for '{topic}'")
            return target_path
    except Exception as e:
        print(f"[ImageGenerator] Pollinations fallback error: {e}")

    return ""

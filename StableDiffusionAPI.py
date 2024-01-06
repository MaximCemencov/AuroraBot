import requests
import io
import base64
from PIL import Image, PngImagePlugin


def RenderImage(Prompt: str, Steps: int = 70, Width: int =  1024, Height: int = 1024, cfg_scale: int = 7):
    url = "http://127.0.0.1:7860"
    payload = {
        "prompt": Prompt,
        "steps": Steps,
        "width": Width,
        "height": Height,
        "cfg_scale": cfg_scale,
    }
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()
    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))
        # image.save('./images/image.png', pnginfo=pnginfo)
        return image
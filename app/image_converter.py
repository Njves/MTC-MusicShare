from PIL import Image

def compress_image(path: str):
    img = Image.open(path)
    img = img.convert('RGB', colors=24)
    img.save(path)

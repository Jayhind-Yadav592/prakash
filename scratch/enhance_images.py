import os
import sys
import glob
import shutil
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
    session = new_session("u2netp")
    print("[INFO] Rembg initialized successfully with u2netp session.")
except Exception as e:
    REMBG_AVAILABLE = False
    session = None
    print(f"[WARN] Rembg not available: {e}")

MEDIA_ROOT = os.path.abspath("media/category_images")
BACKUP_ROOT = os.path.abspath("media/category_images_backup")
TARGET_SIZE = (1200, 1200)

def smart_remove_background(img: Image.Image) -> Image.Image:
    """
    Removes background using AI rembg or smart alpha segmentation.
    Returns RGBA Image with transparent background around the subject.
    """
    # If image already has alpha channel with transparency
    if img.mode == 'RGBA':
        arr = np.array(img)
        alpha = arr[:, :, 3]
        if np.count_nonzero(alpha < 240) > (alpha.size * 0.05):
            # Already transparent cutout!
            return img

    img_rgba = img.convert("RGBA")
    
    if REMBG_AVAILABLE:
        try:
            # Fast, high-accuracy AI cutout
            cutout = remove(img_rgba, session=session, post_process_mask=True)
            return cutout
        except Exception as err:
            print(f"  [AI Rembg Exception]: {err}")
    
    # Fallback to smart color keying
    arr = np.array(img_rgba)
    h, w, _ = arr.shape
    corners = [arr[0, 0], arr[0, w-1], arr[h-1, 0], arr[h-1, w-1]]
    avg_bg = np.mean(corners, axis=0)[:3]
    rgb = arr[:, :, :3]
    diff = np.sqrt(np.sum((rgb - avg_bg) ** 2, axis=-1))
    mask = (diff > 25).astype(np.uint8) * 255
    arr[:, :, 3] = np.minimum(arr[:, :, 3], mask)
    return Image.fromarray(arr)

def enhance_and_frame(img: Image.Image, target_size=(1200, 1200)) -> Image.Image:
    """
    - Crops transparent bounding box cleanly
    - Centers subject onto high-res square canvas with professional margins
    - Upscales via high-quality Lanczos resampling
    - Applies unsharp mask and contrast/color boosting for HD pharmaceutical clarity
    """
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        
    w, h = img.size
    max_w, max_h = int(target_size[0] * 0.86), int(target_size[1] * 0.86)
    scale = min(max_w / w, max_h / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    
    # 1. High-quality Lanczos upscale
    resized = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    
    # 2. Unsharp Mask to sharpen pharmaceutical text, labels, blisters, capsules
    sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1.8, percent=145, threshold=2))
    
    # 3. Contrast, Sharpness and Color Boost for rich studio appearance
    enh_contrast = ImageEnhance.Contrast(sharpened)
    enhanced = enh_contrast.enhance(1.08)
    
    enh_sharp = ImageEnhance.Sharpness(enhanced)
    enhanced = enh_sharp.enhance(1.18)
    
    enh_color = ImageEnhance.Color(enhanced)
    enhanced = enh_color.enhance(1.06)
    
    # 4. Canvas Placement
    canvas = Image.new("RGBA", target_size, (255, 255, 255, 0))
    offset_x = (target_size[0] - new_w) // 2
    offset_y = (target_size[1] - new_h) // 2
    canvas.paste(enhanced, (offset_x, offset_y), mask=enhanced.split()[3])
    
    return canvas

def process_all_images():
    print(f"Starting HD Image Processing across: {MEDIA_ROOT}")
    
    if not os.path.exists(BACKUP_ROOT):
        print(f"Creating backup at: {BACKUP_ROOT}")
        shutil.copytree(MEDIA_ROOT, BACKUP_ROOT)
        print("Backup created successfully.")
        
    image_files = glob.glob(os.path.join(MEDIA_ROOT, "**/*.*"), recursive=True)
    valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".jfif"}
    targets = [f for f in image_files if os.path.splitext(f)[1].lower() in valid_exts]
    
    total = len(targets)
    print(f"Found {total} genuine medical product images to enhance.\n")
    
    success_count = 0
    
    for idx, file_path in enumerate(targets, 1):
        rel_path = os.path.relpath(file_path, MEDIA_ROOT)
        try:
            orig_img = Image.open(file_path)
            orig_size = orig_img.size
            
            # 1. Background removal / segmentation
            cutout = smart_remove_background(orig_img)
            
            # 2. HD Centering, Upscaling & Sharpening
            hd_img = enhance_and_frame(cutout, target_size=TARGET_SIZE)
            
            # 3. Save directly in high-res format
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in [".png"]:
                hd_img.save(file_path, format="PNG", optimize=True)
            elif ext in [".webp"]:
                hd_img.save(file_path, format="WEBP", quality=96, method=6)
            elif ext in [".jpg", ".jpeg"]:
                bg = Image.new("RGB", TARGET_SIZE, (255, 255, 255))
                bg.paste(hd_img, (0, 0), mask=hd_img.split()[3])
                bg.save(file_path, format="JPEG", quality=96, optimize=True, subsampling=0)
            elif ext in [".avif"]:
                try:
                    hd_img.save(file_path, format="AVIF", quality=95)
                except Exception:
                    bg = Image.new("RGB", TARGET_SIZE, (255, 255, 255))
                    bg.paste(hd_img, (0, 0), mask=hd_img.split()[3])
                    bg.save(file_path, format="JPEG", quality=96)
            else:
                hd_img.save(file_path, quality=95)
                
            success_count += 1
            if idx % 10 == 0 or idx == total:
                print(f"[{idx}/{total}] Processed: {rel_path} ({orig_size} -> {TARGET_SIZE})")
                
        except Exception as e:
            print(f"[{idx}/{total}] [ERROR] {rel_path}: {e}")
            
    print(f"\n[SUCCESS] Completed {success_count}/{total} images enhanced to 1200x1200px 2K HD studio quality!")

if __name__ == "__main__":
    process_all_images()

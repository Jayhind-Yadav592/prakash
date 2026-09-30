import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def process_single_image(input_path, output_path, target_size=(1400, 1400)):
    # 1. Read with PIL and OpenCV
    pil_img = Image.open(input_path)
    
    # If image already has alpha channel and genuine transparency
    if pil_img.mode == 'RGBA':
        arr = np.array(pil_img)
        alpha = arr[:, :, 3]
        if np.any(alpha < 250):
            # Already transparent, crop bounding box cleanly
            bbox = pil_img.getbbox()
            if bbox:
                pil_img = pil_img.crop(bbox)
            return finish_hd_canvas(pil_img, target_size, output_path)

    # Convert to RGB
    pil_rgb = pil_img.convert('RGB')
    cv_img = np.array(pil_rgb)
    cv_img_bgr = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
    
    h, w, _ = cv_img.shape
    
    # 2. Detect Background: Sample 4 border strips
    top = cv_img[:max(3, int(h*0.04)), :]
    bot = cv_img[h-max(3, int(h*0.04)):, :]
    left = cv_img[:, :max(3, int(w*0.04))]
    right = cv_img[:, w-max(3, int(w*0.04)):]
    
    border_pixels = np.vstack([
        top.reshape(-1, 3),
        bot.reshape(-1, 3),
        left.reshape(-1, 3),
        right.reshape(-1, 3)
    ])
    
    bg_mean = np.mean(border_pixels, axis=0)
    bg_std = np.std(border_pixels, axis=0)
    
    # Color distance from border background
    diff = np.sqrt(np.sum((cv_img.astype(float) - bg_mean) ** 2, axis=2))
    
    # If border is uniform (std < 40), perform smart background removal
    is_uniform_bg = np.max(bg_std) < 45
    
    if is_uniform_bg and np.mean(bg_mean) > 180: # Light / White / Gray background
        # Threshold difference: background pixels have small diff
        threshold = max(22.0, np.mean(bg_std) * 2.2)
        mask = (diff > threshold).astype(np.uint8) * 255
        
        # Morphological clean up to remove specks & fill internal holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Smooth mask edges with bilateral / Gaussian blur
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        
        # Find the largest contour (the medicine packaging)
        contours, _ = cv2.findContours((mask > 128).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            clean_mask = np.zeros_like(mask)
            cv2.drawContours(clean_mask, [c], -1, 255, -1)
            # Dilate slightly so we don't cut into product edges
            clean_mask = cv2.dilate(clean_mask, kernel, iterations=1)
            clean_mask = cv2.GaussianBlur(clean_mask, (5, 5), 0)
            
            # Combine RGBA
            rgba = np.dstack([cv_img, clean_mask])
            res_pil = Image.fromarray(rgba, 'RGBA')
            
            bbox = res_pil.getbbox()
            if bbox and (bbox[2]-bbox[0] > 20) and (bbox[3]-bbox[1] > 20):
                res_pil = res_pil.crop(bbox)
                return finish_hd_canvas(res_pil, target_size, output_path)

    # If background couldn't be cleanly keyed out without losing detail, crop border & enhance
    return finish_hd_canvas(pil_rgb, target_size, output_path)

def finish_hd_canvas(subject_img, target_size, output_path):
    w, h = subject_img.size
    max_w, max_h = int(target_size[0] * 0.86), int(target_size[1] * 0.86)
    scale = min(max_w / w, max_h / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    
    # 1. Super-Resolution Lanczos Upscale
    resized = subject_img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    
    # 2. Lab-Grade Unsharp Mask for Crisp Text & Drug Details
    sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1.8, percent=145, threshold=2))
    
    # 3. Dynamic Contrast & Sharpness Boost
    enh_contrast = ImageEnhance.Contrast(sharpened)
    enhanced = enh_contrast.enhance(1.08)
    
    enh_sharp = ImageEnhance.Sharpness(enhanced)
    enhanced = enh_sharp.enhance(1.18)
    
    enh_color = ImageEnhance.Color(enhanced)
    enhanced = enh_color.enhance(1.06)
    
    # 4. Center on pure crisp canvas
    ext = os.path.splitext(output_path)[1].lower()
    
    if enhanced.mode == 'RGBA':
        canvas = Image.new("RGBA", target_size, (255, 255, 255, 0))
        offset = ((target_size[0] - new_w) // 2, (target_size[1] - new_h) // 2)
        canvas.paste(enhanced, offset, mask=enhanced.split()[3])
        
        if ext in ['.jpg', '.jpeg']:
            bg = Image.new("RGB", target_size, (255, 255, 255))
            bg.paste(canvas, (0, 0), mask=canvas.split()[3])
            bg.save(output_path, format="JPEG", quality=96, optimize=True, subsampling=0)
        elif ext == '.webp':
            canvas.save(output_path, format="WEBP", quality=96, method=6)
        else:
            canvas.save(output_path, format="PNG", optimize=True)
    else:
        bg = Image.new("RGB", target_size, (255, 255, 255))
        offset = ((target_size[0] - new_w) // 2, (target_size[1] - new_h) // 2)
        bg.paste(enhanced, offset)
        if ext in ['.jpg', '.jpeg']:
            bg.save(output_path, format="JPEG", quality=96, optimize=True, subsampling=0)
        elif ext == '.webp':
            bg.save(output_path, format="WEBP", quality=96, method=6)
        else:
            bg.save(output_path, format="PNG", optimize=True)

    return True

if __name__ == '__main__':
    # Test on a few sample files
    samples = [
        'media/category_images/antidepressants-medicine/ABILIFY.webp',
        'media/category_images/cancer/ABIRAPRO.avif',
        'media/category_images/pain-relief/ALEVE.jpg'
    ]
    for s in samples:
        if os.path.exists(s):
            out = s.replace('media/', 'scratch/')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            process_single_image(s, out)
            print(f"Processed sample {s} -> {out} (Size: {Image.open(out).size})")

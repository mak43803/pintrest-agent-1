from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
import numpy as np
from pathlib import Path
from tools.image_tools import ImageTools

def normalize_and_crop_product_image_v3(img: Image.Image) -> Image.Image:
    """
    Robust, precision auto-cropping:
    1. Detect background color by sampling 4 corner regions.
    2. Compute Euclidean color distance from median background color.
    3. Filter out rows/columns with negligible foreground density (noise rejection).
    4. Return tightly cropped product with 2% safety padding.
    """
    try:
        img_rgba = img.convert("RGBA")
        arr = np.array(img_rgba)
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

        h, w = arr.shape[:2]
        c_size = min(15, max(3, h // 15), max(3, w // 15))
        c_top_left = arr[:c_size, :c_size, :3].reshape(-1, 3)
        c_top_right = arr[:c_size, -c_size:, :3].reshape(-1, 3)
        c_bot_left = arr[-c_size:, :c_size, :3].reshape(-1, 3)
        c_bot_right = arr[-c_size:, -c_size:, :3].reshape(-1, 3)

        corners = np.vstack([c_top_left, c_top_right, c_bot_left, c_bot_right])
        bg_r = np.median(corners[:, 0])
        bg_g = np.median(corners[:, 1])
        bg_b = np.median(corners[:, 2])

        # Distance from background color
        dist = np.sqrt((r.astype(float) - bg_r)**2 + (g.astype(float) - bg_g)**2 + (b.astype(float) - bg_b)**2)

        # Foreground mask: pixel color distance > 16 from background AND alpha > 20
        fg_mask = (dist > 16) & (a > 20)

        # Row & Column pixel density threshold (require at least 0.3% of row/col length or 3px)
        min_row_px = max(3, int(w * 0.003))
        min_col_px = max(3, int(h * 0.003))

        valid_rows = np.where(fg_mask.sum(axis=1) >= min_row_px)[0]
        valid_cols = np.where(fg_mask.sum(axis=0) >= min_col_px)[0]

        if len(valid_rows) > 0 and len(valid_cols) > 0:
            y_min, y_max = valid_rows[0], valid_rows[-1]
            x_min, x_max = valid_cols[0], valid_cols[-1]

            crop_w = x_max - x_min
            crop_h = y_max - y_min
            pad_x = max(6, int(crop_w * 0.02))
            pad_y = max(6, int(crop_h * 0.02))

            x_min = max(0, x_min - pad_x)
            y_min = max(0, y_min - pad_y)
            x_max = min(w, x_max + pad_x)
            y_max = min(h, y_max + pad_y)

            return img.crop((x_min, y_min, x_max, y_max))

        return img
    except Exception as e:
        print("Crop error:", e)
        return img

# Test generating pin for 1565 using raw download image or latest generated pin base
im_raw = Image.open('images/f8147e04.jpg')
print("Raw image size:", im_raw.size)
cropped = normalize_and_crop_product_image_v3(im_raw)
print("Cropped size:", cropped.size)

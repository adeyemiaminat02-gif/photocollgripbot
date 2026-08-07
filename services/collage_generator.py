import math
import logging
from typing import List, Tuple
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

SPACING_MAP = {
    "Small": 10,
    "Medium": 20,
    "Large": 40
}

BG_COLOR_MAP = {
    "White": (255, 255, 255),
    "Black": (0, 0, 0)
}

QUALITY_CELL_SIZE = {
    "Standard": 600,
    "High": 1000
}

def parse_grid_dimensions(grid_str: str) -> Tuple[int, int]:
    try:
        cols, rows = map(int, grid_str.split("x"))
        return cols, rows
    except Exception:
        return 2, 2

def create_collage(
    image_paths: List[str],
    output_path: str,
    grid_size: str = "2x2",
    spacing_name: str = "Medium",
    bg_name: str = "White",
    quality_name: str = "High"
) -> str:
    """Generates a grid photo collage based on configuration options."""
    if not image_paths:
        raise ValueError("No images provided for collage generation.")

    cols, rows = parse_grid_dimensions(grid_size)
    cell_size = QUALITY_CELL_SIZE.get(quality_name, 1000)
    spacing = SPACING_MAP.get(spacing_name, 20)
    bg_color = BG_COLOR_MAP.get(bg_name, (255, 255, 255))

    canvas_width = cols * cell_size + (cols + 1) * spacing
    canvas_height = rows * cell_size + (rows + 1) * spacing

    canvas = Image.new("RGB", (canvas_width, canvas_height), color=bg_color)

    max_cells = cols * rows
    process_paths = image_paths[:max_cells]

    for index, img_path in enumerate(process_paths):
        row = index // cols
        col = index % cols

        x = spacing + col * (cell_size + spacing)
        y = spacing + row * (cell_size + spacing)

        try:
            with Image.open(img_path) as img:
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                fitted_img = ImageOps.fit(img, (cell_size, cell_size), Image.Resampling.LANCZOS)
                canvas.paste(fitted_img, (x, y))
        except Exception as e:
            logger.error(f"Error processing image {img_path}: {e}")
            placeholder = Image.new("RGB", (cell_size, cell_size), color=(200, 200, 200))
            canvas.paste(placeholder, (x, y))

    save_quality = 92 if quality_name == "High" else 80
    canvas.save(output_path, "JPEG", quality=save_quality, optimize=True)
    return output_path

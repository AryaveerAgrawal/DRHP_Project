from pdf2image import convert_from_path
import pytesseract
import os

def process_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        images = convert_from_path(file_path)
        first_image = images[0]
        temp_image_path = file_path.replace(".pdf", ".jpg")
        first_image.save(temp_image_path, "JPEG")
        raw_text = pytesseract.image_to_string(first_image)
        return temp_image_path, raw_text

    elif ext in [".md", ".txt"]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        return None, raw_text  # No image path for text files

    elif ext in [".jpg", ".jpeg", ".png"]:
        raw_text = pytesseract.image_to_string(file_path)
        return file_path, raw_text

    else:
        raise ValueError(f"Unsupported file type: {ext}")

# Keep old name as alias for backward compatibility
def process_pdf(file_path):
    return process_file(file_path)
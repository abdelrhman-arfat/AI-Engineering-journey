from lib.common.logger import Logger
from lib.documents.interfaces.ImageReadersInterface import ImageReadersInterface
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
import base64
import io


class ImageReader(ImageReadersInterface):
    def __init__(self):
        self.service_name = "ImageReader"

    def convert_to_base64(self, image):
        try:
            png_buffer = io.BytesIO()
            image.save(png_buffer, format="PNG")
            png_buffer.seek(0)
            base64_png = base64.b64encode(png_buffer.read()).decode("utf-8")
            data_uri = f"data:image/png;base64,{base64_png}"
            return data_uri
        except Exception as e:
            Logger.error(f"Error converting image to base64: {e}", self.service_name)
            raise ValueError(f"Error converting image to base64: {e}")

    def extract_images(self, file_path: str):
        try:
            images = convert_from_path(file_path)
            return [self.convert_to_base64(image) for image in images]
        except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as e:
            Logger.error(f"Error extracting images: {e}", self.service_name)
            raise ValueError(f"Error extracting images: {e}")

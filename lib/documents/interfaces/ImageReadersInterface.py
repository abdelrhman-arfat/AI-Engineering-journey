from abc import ABC, abstractmethod


class ImageReadersInterface(ABC):
    @abstractmethod
    def extract_images(self, file_path: str):
        pass

    @abstractmethod
    def convert_to_base64(self, image):
        pass

from abc import ABC, abstractmethod


class PdfReadersInterface(ABC):
    @abstractmethod
    def extract_data(self, file_path: str):
        pass

    @abstractmethod
    def clean_text(self, text: str) -> str:
        pass

    @abstractmethod
    def convet_to_json(self, file_path: str):
        pass

from lib.common.logger import Logger
from lib.documents.interfaces.PdfReadersInterface import PdfReadersInterface
from lib.common.responses import Response
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import logging

logging.basicConfig(level=logging.INFO)


class PdfReader(PdfReadersInterface):

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.pages = []
        self.service_name = "PDFReader"

    # ---------------------------------------------------
    # Clean Text
    # ---------------------------------------------------
    def clean_text(self, text: str) -> Response[str]:
        try:
            text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
            text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
            text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

            if "REFERENCES" in text.upper():
                text = re.split(r"REFERENCES", text, flags=re.IGNORECASE)[0]

            text = re.sub(r" +", " ", text)

            return Response.ok(text.strip(), "Text cleaned successfully")

        except Exception as e:
            Logger.error(f"Error cleaning text: {e}", self.service_name)
            return Response.fail(str(e), "Failed to clean text")

    # ---------------------------------------------------
    # Extract Data
    # ---------------------------------------------------
    def extract_data(self, file_path: str) -> Response[dict]:
        try:
            logging.info(f"Loading PDF: {file_path}")

            loader = PyPDFLoader(file_path)
            raw_documents = loader.load()

            if not raw_documents:
                raise ValueError("PDF contains no readable pages.")

            # Clean each page
            for doc in raw_documents:
                cleaned = self.clean_text(doc.page_content)

                if not cleaned.success:
                    raise Exception(cleaned.error)

                doc.page_content = cleaned.data  # FIXED

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    " ",
                    "\.",
                    "?",
                ],
                length_function=len,
                is_separator_regex=False,
            )

            self.pages = splitter.split_documents(raw_documents)

            json_result = self.convet_to_json(file_path)

            if not json_result.success:
                return json_result

            return Response.ok(
                data=json_result.data, message="PDF processed successfully"
            )

        except FileNotFoundError:
            Logger.error(f"File not found: {file_path}", self.service_name)
            return Response.fail("File not found", "PDF loading failed")

        except Exception as e:
            Logger.error(f"Error processing PDF {file_path}: {e}", self.service_name)
            return Response.fail(str(e), "Failed to process PDF")

    # ---------------------------------------------------
    # Convert To JSON
    # ---------------------------------------------------
    def convet_to_json(self, file_path: str) -> Response[dict]:
        try:
            json_pages = []

            for chunk_num, doc in enumerate(self.pages, start=1):
                page_num = doc.metadata.get("page", 0) + 1
                chunk_id = f"{file_path}:{page_num}:{chunk_num}"

                json_pages.append(
                    {
                        "id": chunk_id,
                        "page_number": page_num,
                        "chunk_number": chunk_num,
                        "content": doc.page_content,
                        "source": file_path,
                    }
                )

            result = {
                "file": file_path,
                "total_chunks": len(self.pages),
                "pages": json_pages,
            }

            return Response.ok(result, "JSON conversion successful")

        except Exception as e:
            Logger.error(
                f"Error converting PDF to JSON for {file_path}: {e}", self.service_name
            )
            return Response.fail(str(e), "Failed to convert PDF to JSON")

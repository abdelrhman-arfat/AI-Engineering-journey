from lib.Services.LLMService import LLMService
from lib.common.logger import Logger
from lib.wrappers.AsyncWrapper import AsyncWrapper
from concurrent.futures import ThreadPoolExecutor, as_completed
from lib.Services.EmbeddingService import EmbeddingService
from lib.documents.PdfReader import PdfReader
from lib.database.ChormaDB import ChromaDB
import json


class App:
    def __init__(self, file_path: str):
        self.pdfReader = PdfReader(chunk_size=1200, chunk_overlap=250)
        self.file_path = file_path
        self.embeddingService = EmbeddingService()
        self.chromaDB = ChromaDB()
        self.wrapper = AsyncWrapper(service_name="App")
        self.llmService = LLMService()

    def embed_chunk(self, chunk):
        try:
            res = self.wrapper.retry(
                self.embeddingService.embed_query,
                chunk["content"],
                max_tokens=3000,
                service_name="EmbeddingService",
            )

            if not res.success:
                return None

            Logger.info(
                f"Chunk {chunk['id']} embedded successfully | tokens: {res.data['tokens_used']}",
                "App",
            )

            return {
                "id": chunk["id"],
                "embedding": res.data["embedding"],
                "content": chunk["content"],
                "metadata": {
                    "page_number": chunk["page_number"],
                    "chunk_number": chunk["chunk_number"],
                    "source": chunk["source"],
                },
                "tokens": res.data["tokens_used"],
            }

        except Exception as e:
            Logger.error(
                f"Fatal embedding error for chunk {chunk['id']}: {e}",
                "App",
            )
            return None

    def run_embeddings(self):
        """Process PDF chunks and generate embeddings"""
        response = self.pdfReader.extract_data(file_path=self.file_path)
        if not response.success:
            print("Error:", response.error)
            return

        pages = response.data["pages"]

        embeddings_list = []
        total_tokens = 0
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.embed_chunk, chunk) for chunk in pages]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    embeddings_list.append(result)
                    total_tokens += result["tokens"]

        res = self.chromaDB.add(embeddings_list)
        if not res.success:
            print("Error:", res.error)
            return
        Logger.info(
            f"Generated embeddings for {len(embeddings_list)} chunks and total tokens: {total_tokens}",
            "App",
        )

    def query_embeddings(self, question: str, n_results: int = 3):
        """Embed user question and get results from ChromaDB"""

        embedding_res = self.wrapper.retry(
            self.embeddingService.embed_query,
            question,
            max_tokens=3000,
            service_name="EmbeddingService",
        )

        if not embedding_res.success:
            Logger.error("Failed to embed question", "App")
            return

        # Query ChromaDB
        res = self.wrapper.retry(
            self.chromaDB.get,
            embedding_res.data["embedding"],
            n_results=n_results,
            service_name="ChromaDB",
        )

        if not res.success:
            Logger.error("Failed to query ChromaDB", "App")
            return

        data = res.data["documents"][0] or []

        if not data:
            Logger.info("No relevant chunks found.", "App")
            return

        Logger.info(f"Sending {len(data)} chunks to LLM...", "App")

        llmsRes = self.llmService.generate_response_for_pdf_chunks(data, question)

        if not llmsRes.success:
            Logger.error(llmsRes.error or "Unknown LLM error", "App")
            return

        # ANSI colors
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        RESET = "\033[0m"

        print(f"\n{CYAN}========== FINAL ANSWER =========={RESET}\n")
        print(f"{GREEN}{llmsRes.data}{RESET}\n")

        # Save answer to file
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "question": question,
                    "answer": llmsRes.data,
                },
                f,
                ensure_ascii=False,
                indent=4,
            )

    def terminal_menu(self):
        """Terminal menu to choose options"""
        while True:
            print("\nOptions:")
            print("1. Ask a question")
            print("2. Re-run PDF embeddings")
            print("0. Exit")
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                question = input("Enter your question: ").strip()
                if question:
                    self.query_embeddings(question)
            elif choice == "2":
                print("Re-running embeddings...")
                self.run_embeddings()
            elif choice == "0":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Try again.")


if __name__ == "__main__":
    app = App("pdfs/generative_ai_healthcare_guide.pdf")
    app.terminal_menu()

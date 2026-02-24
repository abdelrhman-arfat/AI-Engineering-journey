import chromadb
from lib.common.responses import Response
from lib.common.logger import Logger
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()


class ChromaDB:
    def __init__(self, collection_name="pdf_chunks_v2"):

        self.service_name = "ChromaDB"
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(collection_name)

    def add(self, data: list):
        try:
            contents = []
            metadatas = []
            embeddings = []
            ids = []
            for d in data:
                contents.append(d["content"])
                metadatas.append(d["metadata"])
                embeddings.append(d["embedding"])
                ids.append(d["id"])

            self.collection.add(
                documents=contents, metadatas=metadatas, embeddings=embeddings, ids=ids
            )
            return Response.ok(None, "data added successfully")
        except Exception as e:
            Logger.error(f"Error in adding data to ChromaDB: {e}", self.service_name)
            return Response.fail(str(e), "failed to add data")

    def get(self, query_embedding: str, n_results: int = 5):
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=n_results
            )
            return Response.ok(results, "data retrieved successfully")
        except Exception as e:
            Logger.error(f"Error in getting data from ChromaDB: {e}", self.service_name)
            return Response.fail(str(e), "failed to get data")

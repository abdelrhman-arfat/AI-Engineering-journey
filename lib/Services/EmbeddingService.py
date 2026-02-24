from lib.common.logger import Logger
from lib.Services.interface.EmbeddingsInterface import EmbeddingsInterface
from lib.common.responses import Response
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os
import tiktoken
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)


class EmbeddingService(EmbeddingsInterface):

    def __init__(self, model: str | None = None):
        self.service_name = "EmbeddingService"
        try:
            if model is None:
                model = "models/gemini-embedding-001"

            self.model = model

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=model, api_key=os.getenv("GOOGLE_API_KEY")
            )

            self.enc = tiktoken.get_encoding("cl100k_base")

            Logger.info(
                f"EmbeddingService initialized with model: {model}", self.service_name
            )

        except Exception as e:
            Logger.error(
                f"Failed to initialize EmbeddingService: {e}", self.service_name
            )
            raise e

    def count_tokens(self, query: str | list) -> Response[int]:
        try:
            if isinstance(query, str):
                tokens = len(self.enc.encode(query))

            elif isinstance(query, list):
                tokens = sum(len(self.enc.encode(q)) for q in query)

            else:
                raise ValueError("Query must be string or list of strings")

            return Response.ok(tokens, "Tokens counted successfully")

        except Exception as e:
            Logger.error(f"Token counting failed: {e}", self.service_name)
            return Response.fail(str(e), "Failed to count tokens")

    # ---------------------------------------------------
    # Validate Token Limit
    # ---------------------------------------------------
    def can_send_request(self, query, max_tokens: int = 1024) -> Response[int]:
        token_response = self.count_tokens(query)

        if not token_response.success:
            return token_response

        tokens = token_response.data

        if tokens > max_tokens:
            error_msg = f"Query too long: {tokens} tokens (max: {max_tokens})"
            Logger.warning(error_msg, self.service_name)
            return Response.fail(error_msg, "Token limit exceeded")

        return Response.ok(tokens, "Token validation passed")

    # ---------------------------------------------------
    # Embed Query
    # ---------------------------------------------------
    def embed_query(self, query: str | list, max_tokens: int = 1024) -> Response[dict]:
        try:
            validation = self.can_send_request(query, max_tokens)

            if not validation.success:
                return validation

            tokens = validation.data

            if isinstance(query, str):
                embedding = self.embeddings.embed_query(query)

            elif isinstance(query, list):
                embedding = self.embeddings.embed_documents(query)

            else:
                raise ValueError("Query must be string or list")

            result = {
                "embedding": embedding,
                "tokens_used": tokens,
                "model": self.model,
            }

            Logger.info("Embedding generated successfully", self.service_name)

            return Response.ok(result, "Embedding generated successfully")

        except Exception as e:
            Logger.error(f"Embedding failed: {e}", self.service_name)
            return Response.fail(str(e), "Embedding generation failed")

    # ---------------------------------------------------
    # Get Model Name
    # ---------------------------------------------------
    def get_embedding_model(self) -> str:
        return self.model

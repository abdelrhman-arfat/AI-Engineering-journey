from abc import ABC, abstractmethod


class EmbeddingsInterface(ABC):

    @abstractmethod
    def embed_query(self, query: str | list):
        pass

    @abstractmethod
    def get_embedding_model(self):
        pass

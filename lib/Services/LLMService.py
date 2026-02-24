import json
from lib.common.responses import Response
from lib.common.logger import Logger
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    def __init__(self):
        self.service_name = "LLMService"
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            api_key=os.getenv("GOOGLE_API_KEY"),
            max_tokens=4000,  # increase to handle bigger outputs
            timeout=60,
            max_retries=2,
        )

    def __build_prompt(self, chunks: list[str], question: str):
        """
        Build a system + human prompt that instructs the LLM to process
        all PDF chunks and return clean JSON with summaries and key points.
        """
        system_message = """
        You are an expert AI assistant specialized in analyzing healthcare documents.

        You will receive:
        1) Context chunks extracted from a document.
        2) A user question.

        Your task:
        - Answer the user's question using ONLY the provided context.
        - Do NOT invent information.
        - If the answer is not found in the context, clearly say:
        "The provided document does not contain enough information to answer this question."
        - Provide a clear, professional, well-structured answer.
        - If helpful, organize the answer using bullet points or short paragraphs.
        - Keep the answer concise but informative.
        """
        # Join all chunks into one human message
        context = "\n\n".join(
            [f"[Chunk {i+1}]\n{chunk}" for i, chunk in enumerate(chunks)]
        )

        human_message = f"""
        Context:
        {context}

        User Question:
        {question}

        Please provide the final answer for the user.
        """

        return [
            ("system", system_message),
            ("human", human_message),
        ]

    def generate_response_for_pdf_chunks(
        self, chunks: list[str], question: str
    ) -> Response[list[dict]]:
        """
        Accepts a list of cleaned PDF text chunks, sends them to LLM,
        parses the JSON, and returns a Python list of summaries.
        """
        try:
            prompt = self.__build_prompt(chunks, question)
            response = self.model.invoke(prompt)

            print(response)

            answer_text = response.text.strip()

            # استخراج معلومات التوكنز
            usage = response.usage_metadata
            total_tokens = usage.get("total_tokens", 0) if usage else 0
            input_tokens = usage.get("input_tokens", 0) if usage else 0
            output_tokens = usage.get("output_tokens", 0) if usage else 0

            return Response.ok(answer_text, "PDF processed successfully")
        except json.JSONDecodeError as json_err:
            Logger.error(f"JSON parsing error: {json_err}", self.service_name)
            return Response.fail(str(json_err), "Failed to parse JSON from LLM output")
        except Exception as e:
            Logger.error(f"Error generating response: {e}", self.service_name)
            return Response.fail(str(e), "Failed to process PDF")

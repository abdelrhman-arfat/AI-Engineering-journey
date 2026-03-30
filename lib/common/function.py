from pydantic import BaseModel, Field, create_model
from typing import Callable, Any, Dict
import inspect


class Function:
    """
    Utility class to convert Python functions + Pydantic models
    into JSON schema compatible with LLM Function Calling.
    """

    service_name = "Function"

    @staticmethod
    def generate_model_from_function(func: Callable[..., Any]) -> BaseModel:
        """
        Dynamically generates a Pydantic model based on a function's
        parameters and type annotations.
        """
        signature = inspect.signature(func)
        model_fields = {}

        for param_name, param in signature.parameters.items():
            # Use annotation or fallback to Any
            param_type = (
                param.annotation if param.annotation != inspect.Parameter.empty else Any
            )
            # If default exists, use it; else mark as required (...)
            default_value = (
                param.default if param.default != inspect.Parameter.empty else ...
            )
            model_fields[param_name] = (param_type, default_value)

        # Create a dynamic model name based on the function name
        model_name = (
            "".join(word.capitalize() for word in func.__name__.split("_")) + "Model"
        )
        return create_model(model_name, **model_fields)

    @staticmethod
    def describe_function(func: Callable[..., Any]) -> Dict:
        model: BaseModel = Function.generate_model_from_function(func)
        model_json = model.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "parameters": model_json,
            },
        }

    @staticmethod
    def function_to_json(func: Callable[..., Any], model: BaseModel) -> Dict:
        """
        Converts a Python function + Pydantic model into a JSON-serializable
        dictionary compatible with LLM Function Calling.

        Args:
            func: The Python function.
            model: The Pydantic model representing the function's parameters.

        Returns:
            JSON dictionary describing the function.
        """
        base_model_json = model.model_json_schema()

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "parameters": base_model_json,
            },
        }


# ---------------- Example ----------------
class FunctionToJSONByPydantic(BaseModel):
    question: str = Field(
        ...,
        description="The question user asks the chatbot to get an answer from my database",
    )
    max_token: int = Field(..., description="The max token for LLM to generate answer")

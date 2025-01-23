import openai
import logging
import config

logger = logging.getLogger("OpenAIClient")


class OpenAIClient:
    """
    A class to interact with the OpenAI API for generating responses.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the OpenAI client with an API key and model.
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = self.api_key

    def generate_completion(self, messages, model=None, **kwargs) -> str:
        """
        Generate a completion from OpenAI API for a given user message.
        """
        model = model or "gpt-4o-mini"
        try:
            logger.info(f"Sending message to OpenAI({model}): {messages}")
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            # Extract the AI response
            return response
        except Exception as e:
            logger.error(f"Failed to generate completion: {e}")
            raise


def replica_repr(content, role='user'):
    return {
        "role": role, 
        "content": content
    }

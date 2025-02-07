from .abc import AIFunction
from bot.utils import send_image_response

class PromptDalle3(AIFunction):
    model = "dall-e-3"
    size = "1024x1024"
    quality="standard"
    n = 1

    scheme = {
        "name": "select_model_dallee_3",
        "description": "Selects the dallee-3 model for generating images based on textual prompts",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "image_description": {
                    "type": "string",
                    "description": "A detailed description of the image to generate"
                },
            },
            "additionalProperties": False,
            "required": [
                "image_description"
            ]
        }
        }

    def __call__(self, image_description):
        return self.model_provider.invoke(
            prompt=image_description
        )
    
    def tg_callback(self, bot, chat_id, message_id, ai_response, clock_msg_id):
        url = ai_response.data[0].url
        text = ai_response.data[0].revised_prompt
        return send_image_response(bot, chat_id, message_id, url, clock_msg_id, caption=text)
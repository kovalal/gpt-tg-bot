import os
from tools import load_model_config

BOT_TOKEN = os.getenv("BOT_API_KEY")
if not BOT_TOKEN:
    raise ValueError("BOT_API_KEY is not set in environment variables")

OPENAI_KEY = os.getenv("OPEANAI_API_KEY")
if not OPENAI_KEY:
    raise ValueError("OPEANAI_API_KEY is not set in environment variables")

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL is not set in environment variables")

model_config = load_model_config('settings/models.json')
model_config['default'] = [k for k, v in model_config.items() if v.get('default')][0]

ERROR_CHAT_ID = os.getenv("ERROR_CHAT_ID")
if not ERROR_CHAT_ID:
    raise ValueError("ERROR_CHAT_ID is not set in environment variables")

PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
if not PROVIDER_TOKEN:
    raise ValueError("PROVIDER_TOKEN is not set in environment variables")



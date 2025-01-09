import json
import asyncio
from functools import wraps

def load_model_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    

def run_in_event_loop(coro):
    @wraps(coro)
    def wrapped(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro(*args, **kwargs))
    return wrapped
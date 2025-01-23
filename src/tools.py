import json
import asyncio
import re
import base64
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


def format_and_split_message_for_telegram(message, max_length=4000):
    """
    Formats a message for Telegram Markdown:
    - Splits messages into chunks <= max_length characters.
    - Preserves code blocks enclosed by triple backticks (''' or ```).
    - Converts LaTeX-style mathematical expressions \( ... \) into italicized Markdown text.
    """
    # Regular expression to detect code blocks (enclosed by triple backticks or single quotes)
    code_block_pattern = re.compile(r"'''(.*?)'''|```(.*?)```", re.DOTALL)

    # Regular expression to detect LaTeX-style math expressions \( ... \)
    math_pattern = re.compile(r'\\\((.*?)\\\)')

    # Convert math expressions to italicized Telegram Markdown format
    def replace_math(match):
        return f"_{match.group(1)}_"



    bold_pattern =  re.compile(r'\*\*(.*?)\*\*')
    def replace_bold(match):
        return f"*{match.group(1)}*"

    #message = re.sub(bold_pattern, replace_bold, message)

    header_pattern = re.compile(r'\#+ (.*\n)')

    def replace_header(match):
        return f"*{match.group(1)}*"

    #message = re.sub(header_pattern, replace_header, message)

    # Split the message into text and code segments
    parts = []
    last_index = 0
    for match in code_block_pattern.finditer(message):
        # Add text before the code block
        if match.start() > last_index:
            parts.append((message[last_index:match.start()], False))
        # Add the code block itself
        code_content = match.group(0)
        parts.append((code_content, True))
        # Update the last index to the end of this match
        last_index = match.end()
    # Add any remaining text after the last code block
    if last_index < len(message):
        parts.append((message[last_index:], False))

    # Build chunks with maximum size constraints
    messages = []
    current_chunk = ""
    for part, is_code in parts:
        if is_code:
            # If the current chunk has content, add it as a separate message before adding code
            if current_chunk:
                messages.append(current_chunk)
                current_chunk = ""
            # Code blocks are added as-is since they shouldn't be split
            if len(part) > max_length:
                raise ValueError("A code block exceeds the maximum message length for Telegram.")
            messages.append(part)
        else:
            part = re.sub(math_pattern, replace_math, part)
            part = re.sub(bold_pattern, replace_bold, part)
            part = re.sub(header_pattern, replace_header, part)
            # Split regular text into chunks of max_length
            while len(part) > 0:
                space_left = max_length - len(current_chunk)
                if space_left <= 0:
                    messages.append(current_chunk)
                    current_chunk = ""
                    space_left = max_length
                # Add as much of the part as fits into the current chunk
                current_chunk += part[:space_left]
                part = part[space_left:]

    # Add the last chunk if it's non-empty
    if current_chunk:
        messages.append(current_chunk)

    return messages


async def retrieve_image_base64(bot, file_id: str) -> str:
    try:
        # Get file information from Telegram
        file_info = await bot.get_file(file_id)
        
        # Download the file content into memory
        file_data = await bot.download_file(file_info.file_path)
        
        # Encode the file content as a base64 string
        base64_image = base64.b64encode(file_data.read()).decode("utf-8")
        
        return base64_image
    except Exception as e:
        bot.logger.error(f"Failed to retrieve or encode image: {e}")
        return None

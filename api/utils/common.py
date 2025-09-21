import re

def clean_reply(text: str) -> str:
    # Remove anything inside <think>...</think> (including the tags)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()

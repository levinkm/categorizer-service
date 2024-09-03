import re
from typing import List

def text_processor(text: str) -> List[str]:
    """Process text for TF-IDF vectorization."""
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.split()
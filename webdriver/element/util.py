def make_alphanumeric(text: str) -> str:
    if text.isalnum():
        return text

    return ''.join(char if char.isalnum() else '_' for char in text)

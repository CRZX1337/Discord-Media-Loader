import uuid
import time
from config import CONFIG

# token -> (filepath, expiry_timestamp)
_file_tokens: dict[str, tuple[str, float]] = {}


def generate_file_token(filepath: str) -> str:
    """
    Generate a 24-hour download token for a file.

    Returns the full authenticated download URL that the user can click.
    The token stays valid for re-downloads within the 24-hour window.
    """
    token = str(uuid.uuid4())
    expiry = time.time() + 86400  # 24 hours, matching file lifetime
    _file_tokens[token] = (filepath, expiry)
    base_url = CONFIG.get("BASE_URL", "http://localhost:8080").rstrip("/")
    return f"{base_url}/downloads?token={token}"

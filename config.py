import json
import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# Setup root logger for initial config phase
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MediaBot.Config")

class ConfigLoader:
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        # 1. Load from file
        try:
            with open("config.json", "r") as f:
                self._config = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config.json: {e}. Checking environment variables.")

        # 2. Resolve CHANNEL_ID (Priority: config.json -> os.getenv -> None)
        channel_id = self._config.get("CHANNEL_ID")
        if not channel_id:
            env_channel = os.getenv("CHANNEL_ID")
            if env_channel:
                try:
                    channel_id = int(env_channel)
                    self._config["CHANNEL_ID"] = channel_id
                except ValueError:
                    logger.error("Environment variable CHANNEL_ID is not a valid integer.")
        
        if not channel_id:
            logger.critical("CRITICAL: CHANNEL_ID is missing in both config.json and .env! Shutdown initiated.")
            sys.exit(1)

        # 3. Apply other defaults if missing
        self._config.setdefault("STATUS_ROTATION_SPEED", 10)
        self._config.setdefault("LINK_REGEX", r'(https?://)?(www\.)?(youtube\.com|youtu\.be|tiktok\.com|twitter\.com|x\.com|instagram\.com)/[^\s]+')
        self._config.setdefault("BASE_URL", "http://localhost:8080")

    @property
    def config(self):
        return self._config

# Export the singleton dictionary
CONFIG = ConfigLoader().config

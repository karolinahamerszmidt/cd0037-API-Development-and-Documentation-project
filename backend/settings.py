import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ.get("DB_PATH")

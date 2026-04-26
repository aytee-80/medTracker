import os

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

AI_DEMO_MODE = False
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
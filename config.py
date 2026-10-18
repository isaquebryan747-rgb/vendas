import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0"))

PIX_KEY = os.getenv("PIX_KEY", "")
PIX_KEY_TYPE = os.getenv("PIX_KEY_TYPE", "CPF")
PIX_NAME = os.getenv("PIX_NAME", "BRAVO STUDIO")
PIX_CITY = os.getenv("PIX_CITY", "SAO PAULO")

if not DISCORD_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Variáveis de ambiente essenciais (DISCORD_TOKEN, SUPABASE_URL, SUPABASE_KEY) não foram configuradas!")

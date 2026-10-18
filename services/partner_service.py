from database.db import supabase
import random
import string

def gerar_codigo_parceiro():
    letras = ''.join(random.choices(string.ascii_uppercase, k=3))
    numeros = ''.join(random.choices(string.digits, k=3))
    return f"BRAVO-{letras}{numeros}"

class PartnerService:
    @staticmethod
    def solicitar_parceria(discord_id, pix_key):
        code = gerar_codigo_parceiro()
        data = {
            "discord_id": discord_id,
            "partner_code": code,
            "pix_key": pix_key,
            "status": "PENDING"
        }
        return supabase.table("partners").insert(data).execute()

    @staticmethod
    def buscar_por_codigo(partner_code):
        res = supabase.table("partners").select("*").eq("partner_code", partner_code).execute()
        return res.data[0] if res.data else None
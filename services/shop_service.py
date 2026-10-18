from database.db import supabase
import random
import string

def gerar_codigo_pedido():
    """Gera um código único e legível para o pedido."""
    letras = ''.join(random.choices(string.ascii_uppercase, k=3))
    numeros = ''.join(random.choices(string.digits, k=4))
    return f"BRAVO-{letras}{numeros}"

class ShopService:
    @staticmethod
    def listar_produtos():
        response = supabase.table("products").select("*").eq("is_active", True).execute()
        return response.data

    @staticmethod
    def criar_produto(nome, descricao, preço, categoria, image_url):
        data = {
            "name": nome,
            "description": descricao,
            "price": float(preço),
            "category": categoria,
            "image_url": image_url,
            "is_active": True
        }
        return supabase.table("products").insert(data).execute()

    @staticmethod
    def criar_pedido(customer_id, product_id, amount, partner_code=None):
        code = gerar_codigo_pedido()
        data = {
            "order_code": code,
            "customer_id": customer_id,
            "product_id": product_id,
            "amount": float(amount),
            "status": "PENDING_PAYMENT",
            "partner_code": partner_code
        }
        res = supabase.table("orders").insert(data).execute()
        return res.data[0] if res.data else None
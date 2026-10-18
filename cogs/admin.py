import discord
from discord.ext import commands
from discord import app_commands
from services.shop_service import ShopService
from database.db import supabase
from config import ADMIN_ROLE_ID

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, interaction: discord.Interaction) -> bool:
        # Verifica se o usuário tem o cargo de administrador configurado
        if not ADMIN_ROLE_ID:
            return True # Se não configurou cargo, libera para testes (cuidado em produção)
        role = interaction.guild.get_role(ADMIN_ROLE_ID)
        return role in interaction.user.roles if role else False

    @app_commands.command(name="produto_adicionar", description="Adiciona um novo produto ao catálogo")
    @app_commands.describe(nome="Nome do produto", preco="Preço em reais (ex: 49.90)", descricao="Descrição", categoria="Categoria", imagem_url="URL da imagem")
    async def produto_adicionar(self, interaction: discord.Interaction, nome: str, preco: float, descricao: str, categoria: str, imagem_url: str):
        ShopService.criar_produto(nome, descricao, preco, categoria, imagem_url)
        await interaction.response.send_message(f"✅ Produto **{nome}** criado com sucesso!", ephemeral=True)

    @app_commands.command(name="parceiro_aprovar", description="Aprova um parceiro pendente pelo código")
    @app_commands.describe(partner_code="Código do parceiro (ex: BRAVO-ABC123)")
    async def parceiro_aprovar(self, interaction: discord.Interaction, partner_code: str):
        res = supabase.table("partners").update({"status": "APPROVED"}).eq("partner_code", partner_code.upper()).execute()
        if res.data:
            await interaction.response.send_message(f"✅ Parceiro **{partner_code.upper()}** aprovado com sucesso!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Parceiro não encontrado.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
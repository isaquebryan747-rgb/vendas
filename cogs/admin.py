import discord
from discord.ext import commands
from discord import app_commands
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="produto_adicionar", description="Adiciona um novo produto com link da Kiwify")
    @app_commands.checks.has_permissions(administrator=True)
    async def produto_adicionar(
        self, 
        interaction: discord.Interaction, 
        nome: str, 
        preco: float, 
        url_kiwify: str, 
        descricao: str, 
        categoria: str = "Geral"
    ):
        if not supabase:
            await interaction.response.send_message("❌ Banco de dados desativado.", ephemeral=True)
            return

        try:
            supabase.table("products").insert({
                "name": nome,
                "price": preco,
                "url": url_kiwify,
                "description": descricao,
                "category": categoria
            }).execute()
            
            await interaction.response.send_message(f"✅ Produto **{nome}** adicionado com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao adicionar produto: {e}", ephemeral=True)

    @app_commands.command(name="produto_editar", description="Edita um produto existente pelo ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def produto_editar(
        self, 
        interaction: discord.Interaction, 
        id_produto: int, 
        novo_nome: str = None, 
        novo_preco: float = None, 
        nova_url_kiwify: str = None, 
        nova_descricao: str = None
    ):
        if not supabase:
            await interaction.response.send_message("❌ Banco de dados desativado.", ephemeral=True)
            return

        dados_atualizados = {}
        if novo_nome: dados_atualizados["name"] = novo_nome
        if novo_preco: dados_atualizados["price"] = novo_preco
        if nova_url_kiwify: dados_atualizados["url"] = nova_url_kiwify
        if nova_descricao: dados_atualizados["description"] = nova_descricao

        if not dados_atualizados:
            await interaction.response.send_message("⚠️ Informe ao menos um campo para alterar.", ephemeral=True)
            return

        try:
            supabase.table("products").update(dados_atualizados).eq("id", id_produto).execute()
            await interaction.response.send_message(f"✅ Produto ID `{id_produto}` atualizado com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao atualizar: {e}", ephemeral=True)

    @app_commands.command(name="produto_remover", description="Remove um produto pelo ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def produto_remover(self, interaction: discord.Interaction, id_produto: int):
        if not supabase:
            await interaction.response.send_message("❌ Banco de dados desativado.", ephemeral=True)
            return

        try:
            supabase.table("products").delete().eq("id", id_produto).execute()
            await interaction.response.send_message(f"🗑️ Produto ID `{id_produto}` removido com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao remover: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))

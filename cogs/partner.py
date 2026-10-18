import discord
from discord.ext import commands
from discord import app_commands
from services.partner_service import PartnerService

class PartnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="parceiro", description="Informações sobre o Programa de Parceiros Bravo")
    async def parceiro(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤝 Programa de Parceiros Bravo Studio",
            description=(
                "Divulgue os nossos serviços visuais e fotografias com IA e receba comissões por cada venda realizada através do seu link/código.\n\n"
                "• **Comissão Padrão:** 10% sobre o valor elegível.\n"
                "• **Como participar:** Use o comando `/parceiro solicitar` informando sua Chave Pix.\n"
                "• **Regras:** Proibida autoindicação e spam. Pagamentos realizados manualmente após verificação."
            ),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="parceiro_solicitar", description="Solicita sua entrada no Programa de Parceiros")
    @app_commands.describe(pix_key="Sua chave Pix para recebimento das comissões")
    async def parceiro_solicitar(self, interaction: discord.Interaction, pix_key: str):
        try:
            PartnerService.solicitar_parceria(interaction.user.id, pix_key)
            await interaction.response.send_message("✅ Solicitação enviada com sucesso! Aguarde a aprovação de um administrador.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("⚠️ Você já possui uma solicitação ou ocorreu um erro ao registrar.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PartnerCog(bot))
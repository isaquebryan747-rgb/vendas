import discord
from discord.ext import commands
from discord import app_commands
from services.shop_service import ShopService
from services.partner_service import PartnerService
from utils.pix import gerar_payload_pix
from config import PIX_KEY, PIX_NAME, PIX_CITY

class ShopView(discord.ui.View):
    def __init__(self, produto):
        super().__init__(timeout=180)
        self.produto = produto
        
    @discord.ui.button(label="Comprar Produto", style=discord.ButtonStyle.green, emoji="🛒")
    async def comprar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Pergunta se tem código de parceiro
        modal = PartnerCodeModal(self.produto)
        await interaction.response.send_modal(modal)

class PartnerCodeModal(discord.ui.Modal, title="Finalizar Pedido - Bravo Studio"):
    def __init__(self, produto):
        super().__init__()
        self.produto = produto

    partner_code = discord.ui.TextInput(
        label="Código de Parceiro (Opcional)",
        placeholder="Ex: BRAVO-ABC123",
        required=False,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        code = self.partner_code.value.strip().upper() if self.partner_code.value else None
        
        # Valida parceiro se informado
        if code:
            parceiro = PartnerService.buscar_por_codigo(code)
            if not parceiro or parceiro["status"] != "APPROVED":
                await interaction.followup.send("⚠️ Código de parceiro inválido ou não aprovado. O pedido continuará sem indicação.", ephemeral=True)
                code = None
            elif parceiro["discord_id"] == interaction.user.id:
                await interaction.followup.send("⚠️ Você não pode usar o seu próprio código de parceiro. O pedido continuará sem indicação.", ephemeral=True)
                code = None

        # Cria o pedido no banco
        pedido = ShopService.criar_pedido(
            customer_id=interaction.user.id,
            product_id=self.produto["id"],
            amount=self.produto["price"],
            partner_code=code
        )

        if not pedido:
            await interaction.followup.send("❌ Erro ao gerar o pedido. Tente novamente mais tarde.", ephemeral=True)
            return

        # Gera o Pix Copia e Cola
        payload_pix = gerar_payload_pix(
            chave=PIX_KEY,
            nome=PIX_NAME,
            cidade=PIX_CITY,
            valor=float(self.produto["price"]),
            identificador=pedido["order_code"]
        )

        embed = discord.Embed(
            title=f"🛒 Pedido Criado: {pedido['order_code']}",
            description=(
                f"**Produto:** {self.produto['name']}\n"
                f"**Valor:** R$ {float(self.produto['price']):.2f}\n\n"
                f"Para concluir sua compra, faça o pagamento via **Pix** utilizando a chave abaixo ou o código Copia e Cola."
            ),
            color=discord.Color.gold()
        )
        embed.add_field(name="Chave Pix", value=f"`{PIX_KEY}`", inline=False)
        embed.add_field(name="Pix Copia e Cola", value=f"```text\n{payload_pix}\n```", inline=False)
        embed.set_footer(text="Após o pagamento, um administrador confirmará seu pedido em breve.")

        await interaction.followup.send(embed=embed, ephemeral=True)

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loja", description="Exibe o catálogo de produtos da Bravo Studio")
    async def loja(self, interaction: discord.Interaction):
        produtos = ShopService.listar_produtos()
        
        if not produtos:
            await interaction.response.send_message("Desculpe, não há produtos disponíveis no momento.", ephemeral=True)
            return

        for p in produtos:
            embed = discord.Embed(
                title=p["name"],
                description=p["description"] or "Sem descrição.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Preço", value=f"R$ {float(p['price']):.2f}", inline=True)
            embed.add_field(name="Categoria", value=p["category"] or "Geral", inline=True)
            
            if p["image_url"]:
                embed.set_image(url=p["image_url"])
                
            view = ShopView(p)
            await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message("📦 Catálogo carregado com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ShopCog(bot))

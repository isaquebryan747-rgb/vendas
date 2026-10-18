import discord
from discord.ext import commands
from discord import app_commands
import os
from supabase import create_client, Client

# Configuração da conexão com o Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Lista dos pacotes com links oficiais da Kiwify
PRODUTOS_KIWIFY = [
    {
        "id": "1_img",
        "nome": "1 Imagem",
        "descricao": "Uma modelagem de IA Profissional e realista",
        "preco": "R$ 10,00",
        "url": "https://pay.kiwify.com.br/2319B39"
    },
    {
        "id": "3_img",
        "nome": "3 Imagens",
        "descricao": "Pacote com 3 modelagens de IA Profissionais e realistas",
        "preco": "R$ 25,00",
        "url": "https://pay.kiwify.com.br/PKXZt40"
    },
    {
        "id": "5_img",
        "nome": "5 Imagens (Mais Vendido 🔥)",
        "descricao": "Pacote recomendado com 5 modelagens de IA Profissionais",
        "preco": "R$ 35,00",
        "url": "https://pay.kiwify.com.br/YDrz5qb"
    },
    {
        "id": "10_img",
        "nome": "10 Imagens (Super Oferta 🚀)",
        "descricao": "Pacote completo com 10 modelagens de IA Profissionais",
        "preco": "R$ 60,00",
        "url": "https://pay.kiwify.com.br/ie8Ah1m"
    }
]

class PartnerCodeModal(discord.ui.Modal, title="Código de Parceiro / Indicação"):
    partner_code = discord.ui.TextInput(
        label="Digite o código do parceiro (Opcional)",
        placeholder="Ex: PARCEIRO10",
        required=False,
        max_length=50
    )

    def __init__(self, produto: dict):
        super().__init__()
        self.produto = produto

    async def on_submit(self, interaction: discord.Interaction):
        codigo = self.partner_code.value.strip() if self.partner_code.value else None
        
        # Registra a intenção de compra no Supabase se houver código de parceiro
        if codigo and supabase:
            try:
                supabase.table("intencoes_compra").insert({
                    "user_id": str(interaction.user.id),
                    "user_name": str(interaction.user),
                    "product_id": self.produto["id"],
                    "partner_code": codigo,
                    "price": self.produto["preco"]
                }).execute()
            except Exception as e:
                print(f"[Aviso] Erro ao registrar código de parceiro no banco: {e}")

        # Cria a View com o botão direto da Kiwify
        view = discord.ui.View()
        btn_pay = discord.ui.Button(
            label=f"Pagar {self.produto['preco']} na Kiwify",
            style=discord.ButtonStyle.link,
            url=self.produto["url"],
            emoji="💳"
        )
        view.add_item(btn_pay)

        embed = discord.Embed(
            title=f"🛒 Checkout: {self.produto['nome']}",
            description=(
                f"**Valor:** {self.produto['preco']}\n"
                f"{f'**Código do Parceiro Aplicado:** `{codigo}`' if codigo else ''}\n\n"
                "Clique no botão abaixo para concluir o pagamento com total segurança e privacidade na Kiwify!"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Pagamento via Pix ou Cartão com confirmação rápida.")

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ProductView(discord.ui.View):
    def __init__(self, produto: dict):
        super().__init__(timeout=None)
        self.produto = produto

        # Botão para iniciar o checkout
        btn_buy = discord.ui.Button(
            label="Comprar Produto",
            style=discord.ButtonStyle.success,
            emoji="🛒"
        )
        btn_buy.callback = self.buy_callback
        self.add_item(btn_buy)

    async def buy_callback(self, interaction: discord.Interaction):
        # Abre o Modal para o cliente inserir o código do parceiro antes de gerar o link
        await interaction.response.send_modal(PartnerCodeModal(self.produto))


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="loja", description="Abre a vitrine de pacotes de imagem")
    async def loja(self, interaction: discord.Interaction):
        await interaction.response.defer()

        for prod in PRODUTOS_KIWIFY:
            embed = discord.Embed(
                title=prod["nome"],
                description=prod["descricao"],
                color=discord.Color.blue()
            )
            embed.add_field(name="Preço", value=f"`{prod['preco']}`", inline=True)
            embed.set_footer(text="Privacidade garantida • Checkout Kiwify")

            view = ProductView(prod)
            await interaction.channel.send(embed=embed, view=view)

        await interaction.followup.send("🛍️ Vitrine carregada com sucesso!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))

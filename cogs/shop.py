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


class PartnerCodeModal(discord.ui.Modal, title="Código de Parceiro / Indicação"):
    partner_code = discord.ui.TextInput(
        label="Digite o código do parceiro (Opcional)",
        placeholder="Ex: PARCEIRO10",
        required=False,
        max_length=50
    )

    def __init__(self, produto: dict, channel: discord.TextChannel):
        super().__init__()
        self.produto = produto
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        codigo = self.partner_code.value.strip().upper() if self.partner_code.value else None
        
        # Link padrão do produto (caso não tenha parceiro ou o código não exista)
        link_pagamento = self.produto.get("url", "https://kiwify.com.br")
        parceiro_encontrado = False

        if codigo and supabase:
            try:
                # Busca se existe um link de afiliado cadastrado para este código e este produto
                res = supabase.table("parceiros_links").select("affiliate_url").eq("partner_code", codigo).eq("product_id", self.produto.get("id")).execute()
                
                if res.data and len(res.data) > 0:
                    link_pagamento = res.data[0]["affiliate_url"]
                    parceiro_encontrado = True

                # Registra a intenção de compra vinculada ao parceiro
                supabase.table("intencoes_compra").insert({
                    "user_id": str(interaction.user.id),
                    "user_name": str(interaction.user),
                    "product_id": str(self.produto.get("id")),
                    "partner_code": codigo if parceiro_encontrado else f"{codigo} (Inválido/Padrão)",
                    "price": str(self.produto.get("price")),
                    "status": "pendente"
                }).execute()
            except Exception as e:
                print(f"[Aviso] Erro ao processar parceiro: {e}")

        # Cria os botões para o canal privado
        view = discord.ui.View()
        btn_pay = discord.ui.Button(
            label="Concluir Pagamento na Kiwify",
            style=discord.ButtonStyle.link,
            url=link_pagamento,
            emoji="💳"
        )
        view.add_item(btn_pay)

        btn_close = discord.ui.Button(
            label="Fechar Atendimento",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id="close_ticket"
        )
        
        async def close_callback(inter: discord.Interaction):
            await inter.response.send_message("🔒 Fechando este canal em 5 segundos...", ephemeral=True)
            import asyncio
            await asyncio.sleep(5)
            await inter.channel.delete()

        btn_close.callback = close_callback
        view.add_item(btn_close)

        embed = discord.Embed(
            title=f"🛒 Carrinho: {self.produto.get('name')}",
            description=(
                f"**Valor:** R$ {float(self.produto.get('price', 0)):.2f}\n"
                f"{f'**Parceiro Aplicado:** `{codigo}` ✅' if parceiro_encontrado else (f'**Código Informado:** `{codigo}` (Não encontrado, usando link padrão)' if codigo else '')}\n\n"
                "Clique no botão abaixo para realizar o pagamento seguro. O link de checkout acima já está direcionado corretamente para você!"
            ),
            color=discord.Color.green()
        )
        
        if self.produto.get("image_url"):
            embed.set_thumbnail(url=self.produto.get("image_url"))

        await self.channel.send(f"{interaction.user.mention} Seja bem-vindo ao seu atendimento exclusivo!", embed=embed, view=view)
        await interaction.response.send_message(
            f"🚀 Carrinho criado com sucesso! Acesse seu canal privado aqui: {self.channel.mention}",
            ephemeral=True
        )


class ShopPaginator(discord.ui.View):
    def __init__(self, produtos: list):
        super().__init__(timeout=180)
        self.produtos = produtos
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.produtos) - 1

    def get_embed_and_view(self):
        prod = self.produtos[self.current_page]
        
        embed = discord.Embed(
            title=f"🛍️ {prod.get('name', 'Produto')}",
            description=prod.get('description', 'Sem descrição'),
            color=discord.Color.blue()
        )
        embed.add_field(name="Preço", value=f"**R$ {float(prod.get('price', 0)):.2f}**", inline=True)
        embed.set_footer(text=f"Página {self.current_page + 1} de {len(self.produtos)} • Checkout Seguro Kiwify")
        
        if prod.get("image_url"):
            embed.set_image(url=prod.get("image_url"))
        
        self.clear_items()
        self.add_item(self.prev_page)
        self.add_item(self.next_page)
        
        btn_buy = discord.ui.Button(label="Comprar Produto", style=discord.ButtonStyle.success, emoji="🛒", row=1)
        
        async def buy_callback(interaction: discord.Interaction):
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name="VENDAS")

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            channel_name = f"carrinho-{interaction.user.name.lower()}"
            existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
            
            if existing_channel:
                await interaction.response.send_message(f"⚠️ Você já tem um carrinho aberto aqui: {existing_channel.mention}", ephemeral=True)
                return

            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Compra do usuário {interaction.user.id} - Produto: {prod.get('name')}"
            )

            await interaction.response.send_modal(PartnerCodeModal(prod, ticket_channel))
        
        btn_buy.callback = buy_callback
        self.add_item(btn_buy)
        
        return embed, self

    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed, view = self.get_embed_and_view()
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Próximo ▶️", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.produtos) - 1:
            self.current_page += 1
            self.update_buttons()
            embed, view = self.get_embed_and_view()
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.defer()


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="loja", description="Abre a vitrine paginada de produtos")
    async def loja(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not supabase:
            await interaction.followup.send("❌ Erro: Supabase não configurado.", ephemeral=True)
            return

        response = supabase.table("products").select("*").execute()
        produtos = response.data

        if not produtos:
            await interaction.followup.send("🛍️ Nenhum produto cadastrado no momento.", ephemeral=True)
            return

        paginator = ShopPaginator(produtos)
        embed, view = paginator.get_embed_and_view()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))

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


class OrderRequestModal(discord.ui.Modal, title="Solicitação de Pedido"):
    client_links = discord.ui.TextInput(
        label="Cole aqui os links das imagens / referências",
        style=discord.TextStyle.paragraph,
        placeholder="Ex: https://drive.google.com/... ou links do Imgur/Discord",
        required=True,
        max_length=1000
    )
    partner_code = discord.ui.TextInput(
        label="Código de Parceiro / Indicação (Opcional)",
        placeholder="Ex: PARCEIRO10",
        required=False,
        max_length=50
    )

    def __init__(self, produto: dict, channel: discord.TextChannel, client_user: discord.Member):
        super().__init__()
        self.produto = produto
        self.channel = channel
        self.client_user = client_user

    async def on_submit(self, interaction: discord.Interaction):
        codigo = self.partner_code.value.strip().upper() if self.partner_code.value else None
        links = self.client_links.value.strip()
        
        link_pagamento = self.produto.get("url", "https://kiwify.com.br")
        parceiro_encontrado = False

        if codigo and supabase:
            try:
                res = supabase.table("parceiros_links").select("affiliate_url").eq("partner_code", codigo).eq("product_id", self.produto.get("id")).execute()
                if res.data and len(res.data) > 0:
                    link_pagamento = res.data[0]["affiliate_url"]
                    parceiro_encontrado = True
            except Exception as e:
                print(f"[Aviso] Erro ao buscar parceiro: {e}")

        pedido_id = None
        if supabase:
            try:
                insert_res = supabase.table("intencoes_compra").insert({
                    "user_id": str(self.client_user.id),
                    "user_name": str(self.client_user),
                    "product_id": str(self.produto.get("id")),
                    "partner_code": codigo if parceiro_encontrado else (codigo if codigo else "Nenhum"),
                    "price": str(self.produto.get("price")),
                    "client_links": links,
                    "status": "aguardando_aprovacao"
                }).execute()
                if insert_res.data:
                    pedido_id = insert_res.data[0].get("id")
            except Exception as e:
                print(f"[Aviso] Erro ao salvar intenção: {e}")

        staff_view = discord.ui.View(timeout=None)

        btn_accept = discord.ui.Button(
            label="✅ Aceitar e Liberar Pagamento",
            style=discord.ButtonStyle.success,
            custom_id="accept_order"
        )
        
        btn_close = discord.ui.Button(
            label="🔒 Fechar Atendimento",
            style=discord.ButtonStyle.danger,
            custom_id="close_ticket"
        )

        async def accept_callback(inter: discord.Interaction):
            if not inter.user.guild_permissions.administrator:
                await inter.response.send_message("❌ Apenas a equipa/staff pode aprovar este pedido.", ephemeral=True)
                return

            if supabase and pedido_id:
                try:
                    supabase.table("intencoes_compra").update({"status": "aprovado"}).eq("id", pedido_id).execute()
                except Exception as e:
                    print(f"[Erro] Erro ao atualizar pedido: {e}")

            # Atribui automaticamente o cargo COMPRADORES ao cliente
            role_comprador = discord.utils.get(inter.guild.roles, name="COMPRADORES")
            if role_comprador and self.client_user:
                try:
                    await self.client_user.add_roles(role_comprador)
                except Exception as e:
                    print(f"[Aviso] Não foi possível atribuir o cargo COMPRADORES: {e}")

            btn_accept.disabled = True
            btn_accept.label = "✅ Pedido Aprovado e Cargo Atribuído!"
            
            pay_view = discord.ui.View()
            btn_pay = discord.ui.Button(
                label="Concluir Pagamento na Kiwify",
                style=discord.ButtonStyle.link,
                url=link_pagamento,
                emoji="💳"
            )
            pay_view.add_item(btn_pay)
            pay_view.add_item(btn_close)

            embed_pay = discord.Embed(
                title="🎉 Solicitação Aprovada!",
                description=(
                    f"Seu pedido para **{self.produto.get('name')}** foi aprovado pela equipa!\n"
                    "O cargo **COMPRADORES** foi atribuído ao seu perfil automaticamente.\n\n"
                    f"**Valor:** R$ {float(self.produto.get('price', 0)):.2f}\n"
                    "Clique no botão abaixo para efetuar o pagamento com segurança na Kiwify."
                ),
                color=discord.Color.green()
            )

            await inter.response.edit_message(view=staff_view)
            await self.channel.send(content=f"{self.client_user.mention}", embed=embed_pay, view=pay_view)

        async def close_callback(inter: discord.Interaction):
            await inter.response.send_message("🔒 A fechar este canal em 5 segundos...", ephemeral=True)
            import asyncio
            await asyncio.sleep(5)
            await inter.channel.delete()

        btn_accept.callback = accept_callback
        btn_close.callback = close_callback

        staff_view.add_item(btn_accept)
        staff_view.add_item(btn_close)

        embed_ticket = discord.Embed(
            title=f"📥 Nova Solicitação: {self.produto.get('name')}",
            description=(
                f"**Cliente:** {self.client_user.mention} ({self.client_user.name})\n"
                f"**Valor:** R$ {float(self.produto.get('price', 0)):.2f}\n"
                f"**Parceiro:** `{codigo if codigo else 'Nenhum'}`\n\n"
                f"**🔗 Links Enviados pelo Cliente:**\n```{links}```\n"
                "Aguardando a análise da Staff."
            ),
            color=discord.Color.gold()
        )

        if self.produto.get("image_url"):
            embed_ticket.set_thumbnail(url=self.produto.get("image_url"))

        await self.channel.send(f"{self.client_user.mention} | 🔔 Nova solicitação recebida!", embed=embed_ticket, view=staff_view)
        await interaction.response.send_message(
            f"🚀 Carrinho criado com sucesso! Aceda ao seu canal privado aqui: {self.channel.mention}",
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
        
        async def buy_payload(interaction: discord.Interaction):
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
                await interaction.response.send_message(f"⚠️ Já tem um carrinho aberto aqui: {existing_channel.mention}", ephemeral=True)
                return

            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Compra de {interaction.user.id} - Produto: {prod.get('name')}"
            )

            await interaction.response.send_modal(OrderRequestModal(prod, ticket_channel, interaction.user))
        
        btn_buy.callback = buy_payload
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
            await interaction.followup.send("🛍️ Nenhum produto registado no momento.", ephemeral=True)
            return

        paginator = ShopPaginator(produtos)
        embed, view = paginator.get_embed_and_view()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))

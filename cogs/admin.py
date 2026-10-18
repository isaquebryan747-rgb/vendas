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

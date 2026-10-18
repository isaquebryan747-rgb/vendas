import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN

# Configuração das intenções (Intents) necessárias para o bot funcionar
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class BravoStudioBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Carrega os módulos (cogs) automaticamente
        await self.load_extension("cogs.shop")
        await self.load_extension("cogs.partner")
        await self.load_extension("cogs.admin")
        
        # Sincroniza os comandos slash com o Discord
        try:
            synced = await self.tree.sync()
            print(f"🔄 Sincronizados {len(synced)} comandos slash.")
        except Exception as e:
            print(f"Erro ao sincronizar comandos: {e}")

    async def on_ready(self):
        print(f"========================================")
        print(f"🤖 Bot conectado como: {self.user} (ID: {self.user.id})")
        print(f"🟢 BRAVO STUDIO BOT está online e operando!")
        print(f"========================================")

bot = BravoStudioBot()

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Erro: Token do Discord não encontrado no arquivo .env!")
    else:
        bot.run(DISCORD_TOKEN)
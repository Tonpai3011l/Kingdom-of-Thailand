import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import start_keep_alive

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=INTENTS,
            help_command=None
        )

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        try:
            synced = await self.tree.sync()
            print(f"เชื่อมต่อคำสั่งแล้ว {len(synced)} คำสั่ง")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการซิงค์คำสั่ง: {e}")

    async def on_ready(self):
        print(f'ล็อกอินในชื่อ {self.user} (ID: {self.user.id})')

bot = Client()

if __name__ == '__main__':
    start_keep_alive()
    if not TOKEN:
        print("ข้อผิดพลาด: ไม่พบ DISCORD_TOKEN ในไฟล์ .env")
    else:
        bot.run(TOKEN, log_handler=None)

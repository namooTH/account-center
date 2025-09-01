import discord
from discord.ext import commands
import json
import logging
import asyncio
import sys
import os
from accountmanager import AccountManager

from cryptography.fernet import Fernet

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

class Bot(commands.Bot):
    def __init__(self):
        self.cogsfolder = "cogs"

        intents = discord.Intents.all()
        command_prefix = '!'
        super().__init__(command_prefix=command_prefix, intents=intents)

        # Get bot config from file 
        # this will be accessible through out the whole bot
        with open("config.json", "r") as file: self.config = json.load(file)
        self.token = self.config["token"]

        self.copyparty_conf_path = self.config["copyparty-userconf"]
        self.copyparty_group = self.config["copyparty-group"]
        
        self.host = self.config["host"]
        self.port = self.config["port"]

        self.app_id = self.config["app-id"]
        self.app_secret = self.config["app-secret"]
        self.app_redirect = self.config["app-redirect"]

        # session key
        try:
            with open("key", "x") as file:
                self.key = Fernet.generate_key()
                file.write(self.key.decode())
        except FileExistsError:
            with open("key", "r") as file:
                self.key = file.read().encode()
        

    async def get_account_manager(self):
        self.account_manager = await AccountManager()

    async def _load_cog(self, cog_name):
        try:
            await self.load_extension(cog_name)
            logger.info(f"Loaded {cog_name} cog.")
        except Exception as e:
            logger.error(f"Failed to load cog {cog_name}: {e}")

    async def load_extensions(self):
        for file in os.listdir(self.cogsfolder):
            if file.endswith(".py"):
                cog_name = f"{self.cogsfolder}.{file[:-3]}"
                await self._load_cog(cog_name)

        logger.info("All cogs loaded successfully.")

bot = Bot()

@bot.listen()
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

async def main():
    async with bot:
        await bot.get_account_manager()
        await bot.load_extensions()
        await bot.start(bot.token)

asyncio.run(main())

import discord
from discord.ext import commands

from aiohttp import web
import aiohttp_session
from aiohttp_session import get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from jinja2 import Environment, FileSystemLoader

from accountmanager import AccountManager, Account

import secrets
import discordoauth2

from dataclasses import asdict

import subprocess

env = Environment(loader=FileSystemLoader('templates')) 
template = env.get_template('index.html')


class yourenobody(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.oauthClient = discordoauth2.AsyncClient(self.bot.app_id, secret=self.bot.app_secret, redirect=self.bot.app_redirect)
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.account_manager: AccountManager = self.bot.account_manager

        @self.routes.get("/")
        async def main(request):
            session = await get_session(request)
            token = session.get("token")
            if not token:
                return web.HTTPFound("/login")
            account: Account = await self.account_manager.get_account_from_token(token)
            if not account:
                return web.HTTPFound("/login")
            return web.HTTPFound("/account")

        @self.routes.get('/login')
        async def login(request):
            return web.HTTPFound(self.oauthClient.generate_uri(scope=["identify"]))

        @self.routes.get("/oauth2")
        async def oauth2(request):
            session = await get_session(request)

            code = request.query.get('code')
            access = await self.oauthClient.exchange_code(code)
            identify = await access.fetch_identify()

            guild = self.bot.get_guild(1089557218153738260) # this section is totally hardcoded and im lazy to do something proper for this
            member: discord.Member = guild.get_member(int(identify["id"]))
            has_role = False
            if member:
                for role in member.roles:
                    if role.id == 1089560636742172763:
                        has_role = True
                        break
            if not has_role:
                return web.Response(text="you are not allowed bro, who are you")
            
            account: Account = await self.account_manager.get_account_from_id(identify["id"])
            if not account:
                token = secrets.token_urlsafe(512)
                await self.account_manager.add_account(Account(id=identify["id"], token=token, username=identify["username"], password=secrets.token_urlsafe(24)))
                await self.account_manager.save_copyparty(self.bot.copypartyconf, self.bot.copypartygroup)
                subprocess.call("./reload_copyparty.sh", shell=True)
            else:
                token = account.token

            session["token"] = token

            return web.HTTPFound("/account")
        
        @self.routes.get("/account")
        async def account(request):
            session = await get_session(request)
            token = session.get("token")
            if not token:
                return web.Response(text="ur not locked in")
            account: Account = await self.account_manager.get_account_from_token(token)
            if not account:
                return web.Response(text="your session might be expired, try to login again.")
            return web.Response(text=template.render(asdict(account)), content_type='text/html')

        aiohttp_session.setup(self.app, EncryptedCookieStorage(secret_key=self.bot.key.decode()))
        self.app.add_routes(self.routes)

async def setup(bot):
    command = yourenobody(bot)
    await bot.add_cog(command)
    runner = web.AppRunner(command.app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=6073)
    await site.start()
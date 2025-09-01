from dataclasses import dataclass
import aiosqlite
import asyncinit
# import aiohttp
import asyncio
# import json
# import urllib.parse
# import re

import copypartyconf

@dataclass
class Account:
    id: int
    token: str
    username: str
    password: str

@asyncinit.asyncinit
class AccountManager():
    async def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.db = await aiosqlite.connect("accounts.db")
        await self.db.execute("CREATE TABLE IF NOT EXISTS accounts(id INTEGER NOT NULL, token TEXT NOT NULL, username TEXT NOT NULL, password TEXT NOT NULL)")

    async def construct_user_from_db(self, user):
        if user:
            return Account(id=user[0], token=user[1], username=user[2], password=user[3])
        return

    async def get_account_from_id(self, id: int):
        cursor = await self.db.execute("""SELECT * FROM accounts WHERE id = ?""", (id,))
        user = await cursor.fetchone()
        return await self.construct_user_from_db(user)
    
    async def get_account_from_token(self, token: str):
        cursor = await self.db.execute("""SELECT * FROM accounts WHERE token = ?""", (token,))
        user = await cursor.fetchone()
        return await self.construct_user_from_db(user)

    async def add_account(self, user: Account):
        await self.db.execute("""
            INSERT INTO accounts VALUES(?, ?, ?, ?)
        """, (user.id, user.token, user.username, user.password))
        await self.db.commit()

    async def get_all_accounts(self) -> list[Account]:
        cursor = await self.db.execute("""SELECT * FROM accounts""")
        accounts = []
        users = await cursor.fetchall()
        for user in users:
            accounts.append(await self.construct_user_from_db(user))
        return accounts

    async def save_copyparty(self, path: str, group: str):
        content = await copypartyconf.construct_string_from_accounts(group, await self.get_all_accounts())
        try:
            f = open(path, 'x')
        except FileExistsError:
            f = open(path, 'w')
        f.write(content)
        
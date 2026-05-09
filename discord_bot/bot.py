import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")
BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

access_token: str | None = None

# Maps discord_user_id -> character_id
user_character: dict[int, int] = {}


async def get_token() -> str:
    global access_token
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{DJANGO_API_URL}/auth/login/",
            json={"username": BOT_USERNAME, "password": BOT_PASSWORD},
        ) as resp:
            data = await resp.json()
            access_token = data["access"]
            return access_token


async def api_get(path: str) -> dict | list:
    global access_token
    if not access_token:
        await get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DJANGO_API_URL}{path}", headers=headers) as resp:
            if resp.status == 401:
                await get_token()
                return await api_get(path)
            return await resp.json()


async def api_post(path: str, payload: dict) -> dict:
    global access_token
    if not access_token:
        await get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{DJANGO_API_URL}{path}", json=payload, headers=headers
        ) as resp:
            if resp.status == 401:
                await get_token()
                return await api_post(path, payload)
            return await resp.json()


@bot.event
async def on_ready():
    await get_token()
    print(f"Bot online as {bot.user}")


@bot.command(name="characters")
async def list_characters(ctx):
    """List available characters: !characters"""
    data = await api_get("/characters/")
    if not data:
        await ctx.reply("No characters available.")
        return
    lines = [f"**{c['name']}** — id: `{c['id']}` — mood: {c['mood']}" for c in data]
    await ctx.reply("Available characters:\n" + "\n".join(lines))


@bot.command(name="select")
async def select_character(ctx, character_id: int):
    """Select a character to talk to: !select <id>"""
    data = await api_get("/characters/")
    match = next((c for c in data if c["id"] == character_id), None)
    if not match:
        await ctx.reply(f"Character with id `{character_id}` not found.")
        return
    user_character[ctx.author.id] = character_id
    await ctx.reply(f"Now talking to **{match['name']}**. Use `!talk <message>` to chat.")


@bot.command(name="talk")
async def talk_command(ctx, *, message: str):
    """Talk to your selected character: !talk <message>"""
    character_id = user_character.get(ctx.author.id)
    if not character_id:
        await ctx.reply("No character selected. Use `!characters` to see the list and `!select <id>` to pick one.")
        return
    data = await api_post(f"/characters/{character_id}/talk/", {"message": message})
    if "error" in data:
        await ctx.reply(f"⚠️ {data['error']}")
    else:
        await ctx.reply(data["response"])


@bot.command(name="whoami")
async def whoami(ctx):
    """Check which character you're talking to: !whoami"""
    character_id = user_character.get(ctx.author.id)
    if not character_id:
        await ctx.reply("You haven't selected a character yet. Use `!characters` to see the list.")
        return
    data = await api_get("/characters/")
    match = next((c for c in data if c["id"] == character_id), None)
    if match:
        await ctx.reply(f"You're talking to **{match['name']}** (mood: {match['mood']})")


bot.run(DISCORD_TOKEN)

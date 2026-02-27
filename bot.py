"""
APEX VAULT License Bot — v3.2
FiveM Ready + Rockstar Account generator (email password from .txt)
Start with: python bot.py
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp, time, os
from datetime import timedelta

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN    = "MTQ3NjI2MTg4NzEyODc2ODcwNA.GHUMKd.5qlZKmcjgecgUooZAyQC3qeCy4TZ2vIGWBx0_E"
SERVER_URL   = "http://localhost:5000"
ADMIN_SECRET = "123456789D"
GUILD_ID     = 1414646147808493753
GEN_PASSWORD = "12345678M.!"

# ── Shop link ─────────────────────────────────────────────────────────────────
DOWNLOAD_LINK = "https://apexvault1.mysellauth.com/"

# ── Generator channel ID ──────────────────────────────────────────────────────
GENERATOR_CHANNEL_ID = 1476260968525987943

# ── Stock files ───────────────────────────────────────────────────────────────
FIVEM_FILE    = "fivem_stock.txt"
ROCKSTAR_FILE = "rockstar_stock.txt"

# ── Default webmail fallback ──────────────────────────────────────────────────
WEBMAIL_LINK = "https://outlook.com"

# ── Roles ─────────────────────────────────────────────────────────────────────
OWNER_IDS = [1020319482272567347]

STAFF_ROLES = [
    "owner",
    "WWW.LFDMARKET",
    "BOSS",
    "Upper Management",
    "Management",
    "Staff",
]

ACCESS_ROLES = STAFF_ROLES + ["Access Generator"]

PLAN_COLORS = {
    "1d":       discord.Color.greyple(),
    "7d":       discord.Color.blue(),
    "1m":       discord.Color.green(),
    "lifetime": discord.Color.gold(),
}
PLAN_EMOJI = {"1d": "⏱️", "7d": "📅", "1m": "🗓️", "lifetime": "♾️"}

BOT_BIO = (
    "🛒 **Apex Vault** — The best shop around!\n"
    "💰 Best prices on the market!\n"
    f"🔗 [Buy now]({DOWNLOAD_LINK}) • apexvault1.mysellauth.com"
)

# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
bot  = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ════════════════════════════════════════════════════════════════════════════════
#  STOCK HELPERS
# ════════════════════════════════════════════════════════════════════════════════

def count_lines(filepath: str) -> int:
    if not os.path.exists(filepath):
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def pop_line(filepath: str) -> str | None:
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [l for l in f.readlines() if l.strip()]
    if not lines:
        return None
    first = lines[0].strip()
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines[1:])
    return first


def push_line(filepath: str, line: str):
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.readlines()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(line.strip() + "\n")
        f.writelines(existing)


def add_lines(filepath: str, entries: list[str]):
    with open(filepath, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(entry.strip() + "\n")

# ── General helpers ───────────────────────────────────────────────────────────

def is_staff(interaction: discord.Interaction) -> bool:
    if interaction.user.id in OWNER_IDS:
        return True
    return interaction.user.guild_permissions.administrator

def has_generator_access(interaction: discord.Interaction) -> bool:
    if interaction.user.id in OWNER_IDS:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    names = [r.name for r in interaction.user.roles]
    return "Access Generator" in names


async def staff_only(interaction: discord.Interaction) -> bool:
    if not is_staff(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command!", ephemeral=True
        )
        return False
    return True


async def api(endpoint: str, payload: dict) -> dict:
    payload["admin_secret"] = ADMIN_SECRET
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SERVER_URL}{endpoint}", json=payload,
            timeout=aiohttp.ClientTimeout(total=8)
        ) as resp:
            return await resp.json()


def key_field(key: str) -> str:
    return f"```{key}```"


def footer_text(action: str = "") -> str:
    base = "Apex Vault • apexvault1.mysellauth.com"
    return f"{action} • {base}" if action else base

# ════════════════════════════════════════════════════════════════════════════════
#  GENERATOR EMBED + BUTTONS
# ════════════════════════════════════════════════════════════════════════════════

def build_generator_embed() -> discord.Embed:
    fivem_stock    = count_lines(FIVEM_FILE)
    rockstar_stock = count_lines(ROCKSTAR_FILE)

    embed = discord.Embed(
        title="🎰  APEX VAULT — GENERATOR",
        description=(
            "Click a button below to generate an account.\n"
            "You will receive it **directly in your DM** with all details.\n\n"
            f"🔗 [**Buy licenses on Apex Vault**]({DOWNLOAD_LINK})"
        ),
        color=discord.Color.purple()
    )
    embed.add_field(
        name="📦 Available Stock",
        value=(
            f"🎮 **FiveM Ready Account** — `{fivem_stock}` in stock\n"
            f"🔑 **Rockstar Account** — `{rockstar_stock}` in stock"
        ),
        inline=False
    )
    embed.add_field(
        name="⚠️ Requirements",
        value=(
            "Only members with the **Access Generator** role can use the buttons.\n"
            "Make sure your **DMs are enabled** before generating!"
        ),
        inline=False
    )
    embed.set_footer(text="Apex Vault • apexvault1.mysellauth.com")
    return embed


class GeneratorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎮 FiveM Ready Account",
        style=discord.ButtonStyle.primary,
        custom_id="gen_fivem"
    )
    async def fivem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_generator_access(interaction):
            await interaction.response.send_message(
                "❌ You don't have the **Access Generator** role to use this!",
                ephemeral=True
            )
            return

        account = pop_line(FIVEM_FILE)
        if account is None:
            await interaction.response.send_message(
                "❌ **FiveM Ready Account** is currently **out of stock**!\n"
                "📩 Contact staff for more information.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎮 FiveM Ready Account",
            description=(
                "✅ You have successfully generated a **FiveM Ready Account**!\n\n"
                f"🔗 [**Buy more on Apex Vault**]({DOWNLOAD_LINK})"
            ),
            color=discord.Color.green()
        )
        embed.add_field(name="📋 Account Details", value=f"```{account}```",           inline=False)
        embed.add_field(name="📦 Product",         value="FiveM Ready Account",         inline=True)
        embed.add_field(name="📊 Stock remaining", value=str(count_lines(FIVEM_FILE)),  inline=True)
        embed.add_field(
            name="⚠️ Important",
            value="Do **not** share this account with anyone! If you have issues, open a **ticket**.",
            inline=False
        )
        embed.set_footer(text="Apex Vault • apexvault1.mysellauth.com • Do not share!")

        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message(
                "✅ **FiveM Ready Account** sent to your **DM**! Check your private messages. 📩",
                ephemeral=True
            )
        except discord.Forbidden:
            push_line(FIVEM_FILE, account)
            await interaction.response.send_message(
                "❌ I can't send you a DM!\n"
                "Enable private messages: **Settings → Privacy & Safety → Allow DMs** and try again.",
                ephemeral=True
            )
            return

        await update_generator_message(interaction)

    @discord.ui.button(
        label="🔑 Rockstar Account",
        style=discord.ButtonStyle.danger,
        custom_id="gen_rockstar"
    )
    async def rockstar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_generator_access(interaction):
            await interaction.response.send_message(
                "❌ You don't have the **Access Generator** role to use this!",
                ephemeral=True
            )
            return

        line = pop_line(ROCKSTAR_FILE)
        if line is None:
            await interaction.response.send_message(
                "❌ **Rockstar Account** is currently **out of stock**!\n"
                "📩 Contact staff for more information.",
                ephemeral=True
            )
            return

        parts = line.split(" ", 1)
        if len(parts) != 2:
            push_line(ROCKSTAR_FILE, line)
            await interaction.response.send_message(
                "❌ Internal error reading account. Please notify staff!", ephemeral=True
            )
            return

        email, password = parts[0], parts[1]

        domain = email.split("@")[-1].lower() if "@" in email else ""
        if any(x in domain for x in ["outlook", "hotmail", "live", "msn"]):
            webmail_url  = "https://outlook.com"
            webmail_name = "Outlook"
        elif "gmail" in domain:
            webmail_url  = "https://mail.google.com"
            webmail_name = "Gmail"
        elif "yahoo" in domain:
            webmail_url  = "https://mail.yahoo.com"
            webmail_name = "Yahoo Mail"
        else:
            webmail_url  = WEBMAIL_LINK
            webmail_name = "Webmail"

        embed = discord.Embed(
            title="🔑 Rockstar Account",
            description=(
                "✅ You have successfully generated a **Rockstar Account**!\n"
                "Use the details below to log in.\n\n"
                f"🔗 [**Buy more on Apex Vault**]({DOWNLOAD_LINK})"
            ),
            color=discord.Color.red()
        )
        embed.add_field(name="📧 Email",    value=f"```{email}```",    inline=False)
        embed.add_field(name="🔐 Password", value=f"```{password}```", inline=False)
        embed.add_field(
            name=f"🌐 {webmail_name} — Access Email",
            value=f"[**➜ Open {webmail_name}**]({webmail_url})\n`{webmail_url}`",
            inline=False
        )
        embed.add_field(
            name="🎮 Rockstar Social Club",
            value="[**➜ Login to Rockstar Games**](https://socialclub.rockstargames.com/)",
            inline=False
        )
        embed.add_field(name="📦 Product",         value="Rockstar Account",              inline=True)
        embed.add_field(name="📊 Stock remaining", value=str(count_lines(ROCKSTAR_FILE)), inline=True)
        embed.add_field(
            name="⚠️ Important",
            value=(
                "• **Do not change** the email or password!\n"
                "• **Do not share** this account with anyone!\n"
                "• Having issues? Open a **ticket**."
            ),
            inline=False
        )
        embed.set_footer(text="Apex Vault • apexvault1.mysellauth.com • Do not share!")

        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message(
                "✅ **Rockstar Account** sent to your **DM**! Check your private messages. 📩",
                ephemeral=True
            )
        except discord.Forbidden:
            push_line(ROCKSTAR_FILE, line)
            await interaction.response.send_message(
                "❌ I can't send you a DM!\n"
                "Enable private messages: **Settings → Privacy & Safety → Allow DMs** and try again.",
                ephemeral=True
            )
            return

        await update_generator_message(interaction)


async def update_generator_message(interaction: discord.Interaction):
    try:
        new_embed = build_generator_embed()
        async for msg in interaction.channel.history(limit=20):
            if msg.author == bot.user and msg.embeds and "GENERATOR" in (msg.embeds[0].title or ""):
                await msg.edit(embed=new_embed)
                break
    except Exception:
        pass


async def send_or_update_generator(guild: discord.Guild):
    channel = bot.get_channel(GENERATOR_CHANNEL_ID)
    if not channel:
        print(f"⚠️  Channel with ID {GENERATOR_CHANNEL_ID} not found! Check the ID in config.")
        return

    embed = build_generator_embed()
    view  = GeneratorView()

    existing = None
    async for msg in channel.history(limit=30):
        if msg.author == bot.user and msg.embeds and "GENERATOR" in (msg.embeds[0].title or ""):
            existing = msg
            break

    if existing:
        await existing.edit(embed=embed, view=view)
        print(f"✅  Generator updated in #{channel.name}")
    else:
        await channel.send(embed=embed, view=view)
        print(f"✅  Generator sent to #{channel.name}")


# ════════════════════════════════════════════════════════════════════════════════
#  /uploadstock
# ════════════════════════════════════════════════════════════════════════════════
@tree.command(name="uploadstock", description="Upload a .txt file with accounts to stock")
@app_commands.describe(
    type="Product type",
    file="The .txt file (one account per line)"
)
@app_commands.choices(type=[
    app_commands.Choice(name="🎮 FiveM Ready Account",  value="fivem"),
    app_commands.Choice(name="🔑 Rockstar Account",      value="rockstar"),
])
async def uploadstock(interaction: discord.Interaction, type: str, file: discord.Attachment):
    if not await staff_only(interaction): return
    if not file.filename.endswith(".txt"):
        await interaction.response.send_message("❌ File must be a `.txt` file!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    filepath = FIVEM_FILE if type == "fivem" else ROCKSTAR_FILE
    label    = "FiveM Ready Account" if type == "fivem" else "Rockstar Account"
    emoji    = "🎮" if type == "fivem" else "🔑"

    content = await file.read()
    lines   = [l.strip() for l in content.decode("utf-8").splitlines() if l.strip()]

    if not lines:
        await interaction.followup.send("❌ The file is empty!", ephemeral=True)
        return

    if type == "rockstar":
        invalid = [l for l in lines if len(l.split(" ", 1)) != 2]
        if invalid:
            await interaction.followup.send(
                f"❌ **{len(invalid)} invalid lines** found!\n"
                f"Correct format: `email password` (one space between them)\n"
                f"Invalid example: `{invalid[0]}`",
                ephemeral=True
            )
            return

    stock_before = count_lines(filepath)
    add_lines(filepath, lines)
    stock_after = count_lines(filepath)

    embed = discord.Embed(title=f"✅ Stock Added — {emoji} {label}", color=discord.Color.green())
    embed.add_field(name="📥 Accounts added", value=str(len(lines)),    inline=True)
    embed.add_field(name="📊 Stock before",   value=str(stock_before),  inline=True)
    embed.add_field(name="📦 Stock now",      value=str(stock_after),   inline=True)
    embed.set_footer(text=footer_text(f"Uploaded by {interaction.user}"))
    await interaction.followup.send(embed=embed, ephemeral=True)

    await send_or_update_generator(interaction.guild)


# ════════════════════════════════════════════════════════════════════════════════
#  /setstock
# ════════════════════════════════════════════════════════════════════════════════
@tree.command(name="setstock", description="Clear all stock for a product type (reset to 0)")
@app_commands.describe(type="Product type to reset")
@app_commands.choices(type=[
    app_commands.Choice(name="🎮 FiveM Ready Account",  value="fivem"),
    app_commands.Choice(name="🔑 Rockstar Account",      value="rockstar"),
])
async def setstock(interaction: discord.Interaction, type: str):
    if not await staff_only(interaction): return
    filepath     = FIVEM_FILE if type == "fivem" else ROCKSTAR_FILE
    label        = "FiveM Ready Account" if type == "fivem" else "Rockstar Account"
    emoji        = "🎮" if type == "fivem" else "🔑"
    stock_before = count_lines(filepath)
    open(filepath, "w").close()
    embed = discord.Embed(title=f"🗑️ Stock Reset — {emoji} {label}", color=discord.Color.orange())
    embed.add_field(name="📊 Stock cleared", value=str(stock_before), inline=True)
    embed.add_field(name="📦 Stock now",     value="0",               inline=True)
    embed.set_footer(text=footer_text(f"Reset by {interaction.user}"))
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await send_or_update_generator(interaction.guild)


# ════════════════════════════════════════════════════════════════════════════════
#  /stockinfo
# ════════════════════════════════════════════════════════════════════════════════
@tree.command(name="stockinfo", description="Check current generator stock")
async def stockinfo(interaction: discord.Interaction):
    if not await staff_only(interaction): return
    embed = discord.Embed(title="📊 Generator Stock", color=discord.Color.purple())
    embed.add_field(name="🎮 FiveM Ready Account", value=f"`{count_lines(FIVEM_FILE)}` accounts",    inline=True)
    embed.add_field(name="🔑 Rockstar Account",     value=f"`{count_lines(ROCKSTAR_FILE)}` accounts", inline=True)
    embed.set_footer(text="Apex Vault • apexvault1.mysellauth.com")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ════════════════════════════════════════════════════════════════════════════════
#  LICENSE KEY COMMANDS
# ════════════════════════════════════════════════════════════════════════════════

@tree.command(name="genkey", description="Generate a new license key")
@app_commands.describe(plan="License duration", password="Authorization password", note="Optional note")
@app_commands.choices(plan=[
    app_commands.Choice(name="⏱️  1 Day",      value="1d"),
    app_commands.Choice(name="📅  7 Days",     value="7d"),
    app_commands.Choice(name="🗓️  1 Month",    value="1m"),
    app_commands.Choice(name="♾️  Lifetime",   value="lifetime"),
])
async def genkey(interaction: discord.Interaction, plan: str, password: str, note: str = ""):
    if not await staff_only(interaction): return
    if password != GEN_PASSWORD:
        await interaction.response.send_message("❌ Wrong password!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        data = await api("/admin/generate", {"plan": plan, "note": note or f"generated by {interaction.user}"})
    except Exception as e:
        await interaction.followup.send(f"❌ Server error: `{e}`", ephemeral=True); return
    if not data.get("ok"):
        await interaction.followup.send(f"❌ {data.get('error')}", ephemeral=True); return
    embed = discord.Embed(title=f"{PLAN_EMOJI.get(plan)}  License Key Generated", color=PLAN_COLORS.get(plan))
    embed.description = BOT_BIO
    embed.add_field(name="🔑 Key",     value=key_field(data["key"]),                inline=False)
    embed.add_field(name="📦 Plan",    value=plan.upper(),                           inline=True)
    embed.add_field(name="📅 Expires", value=data["expires"],                        inline=True)
    embed.add_field(name="📥 Shop",    value=f"[**Apex Vault**]({DOWNLOAD_LINK})",  inline=False)
    if note: embed.add_field(name="📝 Note", value=note, inline=False)
    embed.set_footer(text=footer_text(f"Generated by {interaction.user}"))
    try:
        await interaction.user.send(embed=embed)
        await interaction.followup.send(f"✅ Key generated and sent to DM! Plan: **{plan}**", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(embed=embed, ephemeral=True)

@tree.command(name="bulkgen", description="Generate multiple license keys at once (max 20)")
@app_commands.describe(plan="Plan", amount="How many keys (1-20)", password="Authorization password")
@app_commands.choices(plan=[
    app_commands.Choice(name="⏱️  1 Day",      value="1d"),
    app_commands.Choice(name="📅  7 Days",     value="7d"),
    app_commands.Choice(name="🗓️  1 Month",    value="1m"),
    app_commands.Choice(name="♾️  Lifetime",   value="lifetime"),
])
async def bulkgen(interaction: discord.Interaction, plan: str, amount: int, password: str):
    if not await staff_only(interaction): return
    if password != GEN_PASSWORD:
        await interaction.response.send_message("❌ Wrong password!", ephemeral=True); return
    if not 1 <= amount <= 20:
        await interaction.response.send_message("❌ Amount must be between 1 and 20!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        data = await api("/admin/bulkgenerate", {"plan": plan, "count": amount, "note": str(interaction.user)})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    if not data.get("ok"):
        await interaction.followup.send(f"❌ {data.get('error')}", ephemeral=True); return
    keys_list = data["keys"]
    embed = discord.Embed(
        title=f"{PLAN_EMOJI.get(plan)}  {amount} Keys — {plan.upper()}",
        description="```\n" + "\n".join(k["key"] for k in keys_list) + "\n```",
        color=PLAN_COLORS.get(plan)
    )
    embed.add_field(name="📅 Expires", value=keys_list[0]["expires"], inline=True)
    embed.set_footer(text=footer_text(f"Generated by {interaction.user}"))
    try:
        await interaction.user.send(embed=embed)
        await interaction.followup.send(f"✅ {amount} keys sent to DM!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(embed=embed, ephemeral=True)

@tree.command(name="sendkey", description="Generate a key and send it via DM to a user")
@app_commands.describe(plan="Plan", user="Target user", password="Authorization password")
@app_commands.choices(plan=[
    app_commands.Choice(name="⏱️  1 Day",      value="1d"),
    app_commands.Choice(name="📅  7 Days",     value="7d"),
    app_commands.Choice(name="🗓️  1 Month",    value="1m"),
    app_commands.Choice(name="♾️  Lifetime",   value="lifetime"),
])
async def sendkey(interaction: discord.Interaction, plan: str, user: discord.Member, password: str):
    if not await staff_only(interaction): return
    if password != GEN_PASSWORD:
        await interaction.response.send_message("❌ Wrong password!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        data = await api("/admin/generate", {"plan": plan, "note": f"sent by {interaction.user} to {user}"})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    if not data.get("ok"):
        await interaction.followup.send(f"❌ {data.get('error')}", ephemeral=True); return
    key = data["key"]
    embed = discord.Embed(
        title=f"{PLAN_EMOJI.get(plan)}  License Key — APEX VAULT",
        description="You received a license key!\n\n" + BOT_BIO,
        color=PLAN_COLORS.get(plan)
    )
    embed.add_field(name="🔑 Key",     value=key_field(key),         inline=False)
    embed.add_field(name="📦 Plan",    value=plan.upper(),            inline=True)
    embed.add_field(name="📅 Expires", value=data["expires"],         inline=True)
    embed.add_field(name="📨 From",    value=str(interaction.user),   inline=False)
    embed.set_footer(text="Apex Vault • Do not share this key!")
    try:
        await user.send(embed=embed)
        await interaction.followup.send(f"✅ Key sent to **{user.display_name}**'s DM!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(f"⚠️ DMs are disabled!\nKey: ```{key}```", ephemeral=True)

@tree.command(name="revokekey", description="Revoke a license key")
@app_commands.describe(key="Key to revoke")
async def revokekey(interaction: discord.Interaction, key: str):
    if not await staff_only(interaction): return
    await interaction.response.defer(ephemeral=True)
    try: data = await api("/admin/revoke", {"key": key.upper()})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    if data.get("ok"):
        embed = discord.Embed(title="🚫 Key Revoked", color=discord.Color.red())
        embed.add_field(name="🔑 Key",    value=key_field(key.upper()), inline=False)
        embed.add_field(name="⚡ Status", value="🔴 REVOKED",           inline=False)
        embed.set_footer(text=footer_text(f"Revoked by {interaction.user}"))
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(f"❌ {data.get('error', 'Error')}", ephemeral=True)

@tree.command(name="extendkey", description="Extend a key's expiration by X days")
@app_commands.describe(key="The key", days="Number of days to add")
async def extendkey(interaction: discord.Interaction, key: str, days: int):
    if not await staff_only(interaction): return
    if days <= 0:
        await interaction.response.send_message("❌ Days must be positive!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try: data = await api("/admin/extend", {"key": key.upper(), "days": days})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    if data.get("ok"):
        embed = discord.Embed(title="⏳ Key Extended", color=discord.Color.teal())
        embed.add_field(name="🔑 Key",          value=key_field(key.upper()), inline=False)
        embed.add_field(name="➕ Days added",    value=str(days),              inline=True)
        embed.add_field(name="📅 New expiry",    value=data["new_expires"],    inline=True)
        embed.set_footer(text=footer_text(f"Extended by {interaction.user}"))
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(f"❌ {data.get('error')}", ephemeral=True)

@tree.command(name="resethwid", description="Reset the HWID of a key")
@app_commands.describe(key="The key")
async def resethwid(interaction: discord.Interaction, key: str):
    if not await staff_only(interaction): return
    await interaction.response.defer(ephemeral=True)
    try: data = await api("/admin/resethwid", {"key": key.upper()})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    if data.get("ok"):
        embed = discord.Embed(title="🔄 HWID Reset", color=discord.Color.orange())
        embed.add_field(name="🔑 Key",    value=key_field(key.upper()),             inline=False)
        embed.add_field(name="✅ Status", value="HWID cleared — activatable on a new PC", inline=False)
        embed.set_footer(text=footer_text(f"Reset by {interaction.user}"))
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(f"❌ {data.get('error')}", ephemeral=True)

@tree.command(name="keyinfo", description="Detailed info about a license key")
@app_commands.describe(key="The key to check")
async def keyinfo(interaction: discord.Interaction, key: str):
    if not await staff_only(interaction): return
    await interaction.response.defer(ephemeral=True)
    try: data = await api("/admin/info", {"key": key.upper()})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    if not data.get("ok"):
        await interaction.followup.send(f"❌ {data.get('error')}", ephemeral=True); return
    plan = data["plan"]; revoked = data["revoked"]
    color = discord.Color.red() if revoked else PLAN_COLORS.get(plan, discord.Color.blurple())
    embed = discord.Embed(title="🔍 Key Info", color=color)
    embed.add_field(name="🔑 Key",          value=key_field(data["key"]),                        inline=False)
    embed.add_field(name="📦 Plan",         value=plan.upper(),                                   inline=True)
    embed.add_field(name="⚡ Status",       value="🔴 REVOKED" if revoked else "🟢 Active",       inline=True)
    embed.add_field(name="📅 Expires",      value=data["expires"],                                inline=True)
    embed.add_field(name="⏳ Days left",    value=str(data["days_left"]),                         inline=True)
    embed.add_field(name="🗓️ Created",     value=data["created"],                                inline=True)
    embed.add_field(name="⏰ Activated",    value=data["activated"],                              inline=True)
    embed.add_field(name="\u200b",         value="**── Activation Details ──**",                  inline=False)
    embed.add_field(name="💻 HWID",         value=f"`{data['hwid']}`",                            inline=False)
    embed.add_field(name="🌐 IP",           value=data.get("ip_address", "—"),                    inline=True)
    embed.add_field(name="🖥️ PC Name",     value=data.get("pc_name", "—"),                       inline=True)
    embed.add_field(name="👤 Username",     value=data.get("username", "—"),                      inline=True)
    embed.add_field(name="💿 OS",           value=data.get("os_info", "—"),                       inline=True)
    if data.get("note"): embed.add_field(name="📝 Note", value=data["note"], inline=False)
    embed.set_footer(text="Apex Vault license system")
    await interaction.followup.send(embed=embed, ephemeral=True)

@tree.command(name="listkeys", description="Show the last 50 license keys")
async def listkeys(interaction: discord.Interaction):
    if not await staff_only(interaction): return
    await interaction.response.defer(ephemeral=True)
    try: data = await api("/admin/list", {})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    keys = data.get("keys", [])
    if not keys:
        await interaction.followup.send("📭 No keys in the database.", ephemeral=True); return
    lines = [
        f"{'🔴' if k['revoked'] else PLAN_EMOJI.get(k['plan'],'🔑')} `{k['key']}` — **{k['plan']}** {'✅' if k['hwid']!='—' else '⬜'}"
        for k in keys
    ]
    for i, chunk in enumerate([lines[:25], lines[25:]]):
        if not chunk: break
        embed = discord.Embed(
            title=f"🗂️ License Keys ({len(keys)} total)" if i == 0 else "🗂️ (continued)",
            description="\n".join(chunk), color=discord.Color.blurple()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@tree.command(name="searchkey", description="Search for a key by note, user or partial ID")
@app_commands.describe(query="Text to search for")
async def searchkey(interaction: discord.Interaction, query: str):
    if not await staff_only(interaction): return
    await interaction.response.defer(ephemeral=True)
    try: data = await api("/admin/search", {"query": query})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    results = data.get("results", [])
    if not results:
        await interaction.followup.send(f"🔍 No results for: **{query}**", ephemeral=True); return
    lines = [
        f"{'🔴' if r['revoked'] else PLAN_EMOJI.get(r['plan'],'🔑')} `{r['key']}` **{r['plan']}** {'✅' if r['hwid']!='—' else '⬜'} {'_'+r['note']+'_' if r.get('note') else ''}"
        for r in results
    ]
    embed = discord.Embed(
        title=f"🔍 \"{query}\" ({len(results)} found)",
        description="\n".join(lines), color=discord.Color.blurple()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

@tree.command(name="stats", description="General statistics for all licenses")
async def stats(interaction: discord.Interaction):
    if not await staff_only(interaction): return
    await interaction.response.defer(ephemeral=True)
    try: data = await api("/admin/stats", {})
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True); return
    bp = data.get("by_plan", {})
    embed = discord.Embed(title="📊  APEX VAULT — Statistics", color=discord.Color.purple())
    embed.add_field(name="📦 Total Keys",    value=str(data["total"]),     inline=True)
    embed.add_field(name="🟢 Active",        value=str(data["active"]),    inline=True)
    embed.add_field(name="🔴 Revoked",       value=str(data["revoked"]),   inline=True)
    embed.add_field(name="⌛ Expired",       value=str(data["expired"]),   inline=True)
    embed.add_field(name="💻 Activated",     value=str(data["activated"]), inline=True)
    embed.add_field(name="\u200b",           value="\u200b",               inline=True)
    embed.add_field(name="📋 By Plan", value=(
        f"⏱️ 1 Day: **{bp.get('1d',0)}**\n"
        f"📅 7 Days: **{bp.get('7d',0)}**\n"
        f"🗓️ 1 Month: **{bp.get('1m',0)}**\n"
        f"♾️ Lifetime: **{bp.get('lifetime',0)}**"
    ), inline=False)
    embed.add_field(name="🎰 Generator Stock", value=(
        f"🎮 FiveM: **{count_lines(FIVEM_FILE)}**\n"
        f"🔑 Rockstar: **{count_lines(ROCKSTAR_FILE)}**"
    ), inline=False)
    embed.set_footer(text="Apex Vault • apexvault1.mysellauth.com")
    await interaction.followup.send(embed=embed, ephemeral=True)

@tree.command(name="ping", description="Check if the license server is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    t = time.time()
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                SERVER_URL + "/admin/stats",
                json={"admin_secret": ADMIN_SECRET},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                await r.json()
        embed = discord.Embed(title="🟢 Server Online", color=discord.Color.green())
        embed.add_field(name="⚡ Latency", value=f"{int((time.time()-t)*1000)}ms", inline=True)
    except:
        embed = discord.Embed(title="🔴 Server Offline", color=discord.Color.red())
        embed.add_field(name="⚠️ Status", value="Not responding", inline=True)
    embed.set_footer(text="Apex Vault")
    await interaction.followup.send(embed=embed, ephemeral=True)


# ════════════════════════════════════════════════════════════════════════════════
#  MODERATION
# ════════════════════════════════════════════════════════════════════════════════

@tree.command(name="role_add", description="Add a role to a member")
@app_commands.describe(member="The user", role="The role to add")
async def role_add(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not await staff_only(interaction): return
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You need **Manage Roles** permission.", ephemeral=True); return
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ That role is above my highest role.", ephemeral=True); return
    if role in member.roles:
        await interaction.response.send_message(f"{member.mention} already has **{role.name}**.", ephemeral=True); return
    await member.add_roles(role, reason=f"Added by {interaction.user}")
    embed = discord.Embed(title="✅ Role Added", color=discord.Color.green())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Role", value=role.mention,   inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Apex Vault • Moderation")
    await interaction.response.send_message(embed=embed)

@tree.command(name="role_remove", description="Remove a role from a member")
@app_commands.describe(member="The user", role="The role to remove")
async def role_remove(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not await staff_only(interaction): return
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You need **Manage Roles** permission.", ephemeral=True); return
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ That role is above my highest role.", ephemeral=True); return
    if role not in member.roles:
        await interaction.response.send_message(f"{member.mention} doesn't have **{role.name}**.", ephemeral=True); return
    await member.remove_roles(role, reason=f"Removed by {interaction.user}")
    embed = discord.Embed(title="✅ Role Removed", color=discord.Color.red())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Role", value=role.mention,   inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Apex Vault • Moderation")
    await interaction.response.send_message(embed=embed)

@tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(user="The user", reason="Ban reason", delete_days="Delete messages from last X days (0-7)")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
    if not await staff_only(interaction): return
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You can't ban someone with a higher or equal role!", ephemeral=True); return
    try:
        dm = discord.Embed(title="🔨 You have been banned!", description=f"Server: **{interaction.guild.name}**", color=discord.Color.red())
        dm.add_field(name="⚖️ Reason", value=reason, inline=False)
        await user.send(embed=dm)
    except: pass
    await interaction.guild.ban(user, reason=reason, delete_message_days=max(0, min(7, delete_days)))
    embed = discord.Embed(title="🔨 User Banned", color=discord.Color.red())
    embed.add_field(name="👤 User",   value=user.mention, inline=True)
    embed.add_field(name="⚖️ Reason", value=reason,       inline=False)
    embed.add_field(name="👮 By",     value=interaction.user.mention, inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text="Apex Vault • Moderation")
    await interaction.response.send_message(embed=embed)

@tree.command(name="unban", description="Unban a user")
@app_commands.describe(user_id="User ID to unban", reason="Unban reason")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    if not await staff_only(interaction): return
    await interaction.response.defer()
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)
        embed = discord.Embed(title="✅ User Unbanned", color=discord.Color.green())
        embed.add_field(name="👤 User",   value=str(user), inline=True)
        embed.add_field(name="⚖️ Reason", value=reason,    inline=False)
        embed.set_footer(text="Apex Vault • Moderation")
        await interaction.followup.send(embed=embed)
    except ValueError:
        await interaction.followup.send("❌ Invalid ID!", ephemeral=True)
    except discord.NotFound:
        await interaction.followup.send("❌ User is not in the ban list!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True)

@tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(user="The user", reason="Kick reason")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not await staff_only(interaction): return
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You can't kick someone with a higher role!", ephemeral=True); return
    try:
        dm = discord.Embed(title="👢 You have been kicked!", color=discord.Color.orange())
        dm.add_field(name="⚖️ Reason", value=reason, inline=False)
        await user.send(embed=dm)
    except: pass
    await interaction.guild.kick(user, reason=reason)
    embed = discord.Embed(title="👢 User Kicked", color=discord.Color.orange())
    embed.add_field(name="👤 User",   value=user.mention, inline=True)
    embed.add_field(name="⚖️ Reason", value=reason,       inline=False)
    embed.add_field(name="👮 By",     value=interaction.user.mention, inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text="Apex Vault • Moderation")
    await interaction.response.send_message(embed=embed)

@tree.command(name="timeout", description="Timeout a user")
@app_commands.describe(user="The user", minutes="Duration in minutes", reason="Reason")
async def timeout_cmd(interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "No reason provided"):
    if not await staff_only(interaction): return
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You can't timeout someone with a higher role!", ephemeral=True); return
    minutes = max(1, min(40320, minutes))
    duration = f"{minutes}min" if minutes < 60 else (f"{minutes//60}h" if minutes < 1440 else f"{minutes//1440}d")
    await user.timeout(timedelta(minutes=minutes), reason=reason)
    embed = discord.Embed(title="⏱️ Timeout Applied", color=discord.Color.yellow())
    embed.add_field(name="👤 User",      value=user.mention, inline=True)
    embed.add_field(name="⏳ Duration",  value=duration,     inline=True)
    embed.add_field(name="⚖️ Reason",   value=reason,        inline=False)
    embed.add_field(name="👮 By",        value=interaction.user.mention, inline=True)
    embed.set_footer(text="Apex Vault • Moderation")
    await interaction.response.send_message(embed=embed)

@tree.command(name="untimeout", description="Remove a user's timeout")
@app_commands.describe(user="The user", reason="Reason")
async def untimeout_cmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not await staff_only(interaction): return
    await user.timeout(None, reason=reason)
    embed = discord.Embed(title="✅ Timeout Removed", color=discord.Color.green())
    embed.add_field(name="👤 User",    value=user.mention, inline=True)
    embed.add_field(name="⚖️ Reason", value=reason,        inline=False)
    embed.add_field(name="👮 By",      value=interaction.user.mention, inline=True)
    embed.set_footer(text="Apex Vault • Moderation")
    await interaction.response.send_message(embed=embed)

@tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user", reason="Reason")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not await staff_only(interaction): return
    try:
        dm = discord.Embed(title="⚠️ You have been warned!", color=discord.Color.orange())
        dm.add_field(name="⚖️ Reason",    value=reason,                  inline=False)
        dm.add_field(name="👮 Moderator", value=str(interaction.user),   inline=False)
        await user.send(embed=dm)
        dm_status = "✅ Sent"
    except:
        dm_status = "❌ DMs disabled"
    embed = discord.Embed(title="⚠️ User Warned", color=discord.Color.orange())
    embed.add_field(name="👤 User",    value=user.mention, inline=True)
    embed.add_field(name="📨 DM",      value=dm_status,    inline=True)
    embed.add_field(name="⚖️ Reason",  value=reason,       inline=False)
    embed.add_field(name="👮 By",      value=interaction.user.mention, inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text="Apex Vault • Moderation")
    await interaction.response.send_message(embed=embed)

@tree.command(name="myroles", description="Debug: shows your exact role names")
async def myroles(interaction: discord.Interaction):
    names = [r.name for r in interaction.user.roles]
    is_s  = is_staff(interaction)
    embed = discord.Embed(title="🔍 Your Roles", color=discord.Color.blurple())
    embed.add_field(name="📋 Role names", value="\n".join(f"`{n}`" for n in names) or "None", inline=False)
    embed.add_field(name="✅ Is Staff?", value=str(is_s), inline=True)
    embed.add_field(name="🔑 Staff Roles list", value="\n".join(f"`{r}`" for r in STAFF_ROLES), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="helpstaff", description="List of all staff commands")
async def helpstaff(interaction: discord.Interaction):
    if not await staff_only(interaction): return
    embed = discord.Embed(title="📖  APEX VAULT — Staff Commands", description=BOT_BIO, color=discord.Color.purple())
    embed.add_field(name="🎰 Generator (Stock)", value=(
        "`/uploadstock` — Upload a .txt file with accounts\n"
        "`/setstock` — Clear all stock for a type\n"
        "`/stockinfo` — Check current stock"
    ), inline=False)
    embed.add_field(name="🔑 License Keys", value=(
        "`/genkey` `/bulkgen` `/sendkey`\n"
        "`/keyinfo` `/listkeys` `/searchkey`\n"
        "`/revokekey` `/extendkey` `/resethwid`"
    ), inline=False)
    embed.add_field(name="🔨 Moderation", value=(
        "`/ban` `/unban` `/kick`\n"
        "`/timeout` `/untimeout` `/warn`\n"
        "`/role_add` `/role_remove`"
    ), inline=False)
    embed.add_field(name="📊 Info", value="`/stats` `/ping` `/helpstaff`", inline=False)
    embed.set_footer(text="Apex Vault • apexvault1.mysellauth.com")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Events ────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    bot.add_view(GeneratorView())

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="apexvault1.mysellauth.com | Best prices!"
        )
    )

    guild = discord.Object(id=GUILD_ID) if GUILD_ID else None
    if guild:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
    else:
        await tree.sync()

    print(f"✅ Bot started as {bot.user}")
    print(f"   FiveM stock: {count_lines(FIVEM_FILE)} | Rockstar stock: {count_lines(ROCKSTAR_FILE)}")
    print(f"   Generator channel ID: {GENERATOR_CHANNEL_ID}")

    actual_guild = bot.get_guild(GUILD_ID)
    if actual_guild:
        await send_or_update_generator(actual_guild)


# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(BOT_TOKEN)

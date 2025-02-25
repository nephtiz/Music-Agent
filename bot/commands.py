import os
import discord
from discord import app_commands
import asyncio
from dotenv import load_dotenv

from audio.processing import is_valid_wav, resample_audio_inplace
from steganography.lsb import (
    text_to_audio,
    verify_audio_signature,
    audio_to_text,
    generate_random_filename
)

load_dotenv()
token = os.getenv("TOKEN")
signature = os.getenv("SIGNATURE")
updatesCH = int(os.getenv("UPDATES"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
    name="encrypt",
    description="Encrypt a text message"
)
@app_commands.describe(
    input="The text you want to encrypt",
    audio="The audio (.wav file) you want the bot to use",
    password="The password needed for decryption",
    exceptions="The users who do not require a password for decryption"
)
@app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def encrypt(interaction: discord.Interaction, input: str, password: str = None, exceptions: str = None, audio: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)
    if len(input) > 1000:
        embed = discord.Embed(
            title="⚠️ Message Too Long",
            description="Your message exceeds 1000 characters. Please shorten it and try again.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    if password and len(password) > 64:
        embed = discord.Embed(
            title="⚠️ Password Too Long",
            description="Your password exceeds 64 characters. Please shorten it and try again.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    if audio and audio.size > 50 * 1024 * 1024:
        embed = discord.Embed(
            title="⚠️ File Too Large",
            description="The uploaded file exceeds 50MB. Please upload a smaller file and try again.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    if password is None and exceptions is not None:
        embed = discord.Embed(
            title="❌ Invalid Configuration",
            description="You cannot provide exceptions without setting a password first. Please correct and try again.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    mentioned_user_ids = []
    if exceptions:
        mentioned_user_ids = [
            mention[2:-1]
            for mention in exceptions.split()
            if mention.startswith("<@") and mention.endswith(">")
        ]

    # Automatically add the user encrypting the audio to the exceptions list
    if password:
        mentioned_user_ids.append(str(interaction.user.id))
        mentioned_user_ids = list(set(mentioned_user_ids))

        if len(mentioned_user_ids) > 15:
            embed = discord.Embed(
                title="🚫 Too Many Exceptions",
                description="The number of exceptions cannot exceed 15 users. Please reduce the list and try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
    if audio is None:
        audio_path = "./default.wav"
        if not os.path.exists(audio_path):
            embed = discord.Embed(
                title="📁 Default Audio Missing",
                description="The default audio file is not found. Please upload an audio file to proceed.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
    else:
        if not audio.filename.endswith(".wav"):
            embed = discord.Embed(
                title="🔊 Unsupported Format",
                description=(
                    "Only `.wav` audio files are supported. Please convert your audio using a tool like "
                    "[freeconvert.com](https://www.freeconvert.com/wav-converter) and try again."
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        audio_path = f"./{audio.filename}"
        await audio.save(audio_path)

    output_filename = generate_random_filename()
    output_path = f"./{output_filename}"

    try:
        if not is_valid_wav(audio_path):
            embed = discord.Embed(
                title="🚫 Invalid Audio File",
                description=(
                    "The provided audio file is invalid or corrupted. Please ensure it's a valid `.wav` file and try again."
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        await resample_audio_inplace(audio_path)
        text_to_audio(input, audio_path, output_file=output_path, signature=signature, password=password, exceptions=mentioned_user_ids)
        await interaction.followup.send("🔧 Encrypting your message... Please wait.", ephemeral=True)

        if not is_valid_wav(output_path):
            embed = discord.Embed(
                title="An Unexpected Error Occurred with Encrypted Audio",
                description=(
                    "An unexpected error occurred on our side while handling the encrypted audio. "
                    "Please try again and contact the operator if the issue persists."
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        with open(output_path, 'rb') as file:
            att_message = f"Musical message from {interaction.user.mention}"
            if password: att_message = f"Musical message: {interaction.user.mention} → {exceptions}"
            await interaction.followup.send(att_message, file=discord.File(file, output_filename))

    except Exception as e:
        error_message = str(e)
        if "error code: 40005" in error_message or "413 Payload Too Large" in error_message:
            file_size_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            file_size_mb = file_size_bytes / (1024 * 1024)
            embed = discord.Embed(
                title="⚠️ File Too Large",
                description=(
                    f"The encrypted audio file size is **{file_size_mb:.2f} MB**, which exceeds Discord's upload limit.\n\n"
                    "Note: Server boosting increases the upload limit:\n"
                    "• Level 2: 50 MB uploads\n"
                    "• Level 3: 100 MB uploads"
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="⚠️ An Unexpected Error Occurred",
                description=f"```{error_message}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    finally:
        if audio is not None and os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(output_path):
            os.remove(output_path)

@tree.context_menu(name="decrypt")
@app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def decrypt(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=True)
    if not message.attachments:
        embed = discord.Embed(
            title="❌ No Attachments Found",
            description="This message does not contain any attachments. Please provide a valid `.wav` file to decrypt.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    attachment = message.attachments[0]
    if not attachment.filename.endswith(".wav"):
        embed = discord.Embed(
            title="🔊 Unsupported Format",
            description="This attachment is not a valid `.wav` file. Please ensure the file is in the correct format and try again.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    file_path = f"./{attachment.filename}"
    await attachment.save(file_path)

    try:
        if not is_valid_wav(file_path):
            embed = discord.Embed(
                title="🚫 Invalid Audio File",
                description="The provided audio file is invalid or corrupted. Please upload a valid `.wav` file.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if not verify_audio_signature(file_path, signature=signature):
            embed = discord.Embed(
                title="🔍 Verification Failed",
                description="The file is not a valid encrypted audio.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        decryption_result = audio_to_text(file_path, signature=signature)
        if "error" in decryption_result:
                embed = discord.Embed(
                    title="⚠️ Decryption Failed",
                    description=decryption_result["error"],
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        extracted_password = decryption_result.get("password")
        exceptions = decryption_result.get("exceptions")
        exceptions_list = exceptions.split(",") if exceptions else []
        extracted_text = decryption_result.get("text")

        embed = discord.Embed(
            title="🔑 Your Secret Message",
            description=f"```{extracted_text}```",
            color=discord.Color.green()
        )
        embed.set_footer(text="Keep it safe. Secrets like these are precious!")

        if not extracted_password:
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if exceptions_list and user_id in exceptions_list:
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await interaction.followup.send("🔑 Password required. Check your DMs.", ephemeral=True)
        try:
            user = interaction.user
            try:
                dm_channel = await user.create_dm()
                await dm_channel.send("🔑 Please enter the decryption password:")
            except discord.Forbidden:
                await interaction.followup.send("❌ Unable to send you a DM. Please enable DMs from server members and try again.", ephemeral=True)
                return
            except Exception as e:
                await interaction.followup.send("❌ An error occurred while trying to send you a DM. Please try again later.", ephemeral=True)
                return

            def check(msg):
                return msg.author == user and msg.channel == dm_channel and len(msg.content) > 0

            password_message = await interaction.client.wait_for("message", check=check, timeout=60)
            if password_message.content == extracted_password:
                await dm_channel.send(f"✅ Password correct! The secret has been sent to {interaction.channel.mention}.")
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await dm_channel.send("❌ Wrong password. Decryption failed.")

        except asyncio.TimeoutError:
            await user.send("⏰ You took too long to respond. Decryption process aborted.")
            return
    except Exception as e:
        embed = discord.Embed(
            title="⚠️ An Unexpected Error Occurred",
            description=f"```{e}```",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@tree.command(
    name="help",
    description="Receive general intel about the agent"
)
@app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Agent's Mission Briefing 📜",
        description=(
            "Welcome to the Secret Agent's communication network.\n\n"
            "This bot specializes in steganography - the art of hiding messages within audio files. "
            "Your messages are seamlessly concealed within WAV audio files, "
            "making them appear as ordinary sound clips.\n\n"
            "Below are your classified operation protocols."
        ),
        color=discord.Color.blurple()
    )

    embed.add_field(name="\u200b", value="✦・―――――――・✦", inline=False)

    embed.add_field(
        name="🔒 `/encrypt` Command",
        value=(
            "**Mission:** Conceal a secret message within an audio file.\n\n"
            "**Parameters:**\n"
            "• **`input`** *(Required)*: The secret message to hide\n"
            "• **`audio`**: Target WAV file for message concealment\n"
            "‣ *If not provided, a default audio file will be used*\n"
            "‣ *Must be in `.wav` format*\n"
            "• **`password`**: Security key for message protection\n"
            "• **`exceptions`**: Trusted members who can access without password\n\n"
            "**Security Notice:**\n"
            "Messages are hidden using audio steganography. While well-concealed, "
            "they are not currently encrypted. Exercise caution with sensitive information."
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="✦・―――――――・✦", inline=False)

    embed.add_field(
        name="🔓 `Decrypt` Command",
        value=(
            "**Mission:** Extract concealed messages from audio files.\n\n"
            "**Execution Protocol:**\n"
            "1. Locate the target audio file message\n"
            "2. Right-click the message\n"
            "3. Select `Apps` → `Decrypt`\n"
            "4. Enter security key if required\n\n"
            "**Access Levels:**\n"
            "• No password: Message is freely accessible\n"
            "• With password: Security key required\n"
            "• Exception list: Designated members have direct access"
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="✦・―――――――・✦", inline=False)

    embed.add_field(
        name="⚠️ Security Advisory",
        value=(
            "• Steganography conceals messages but does not encrypt them\n"
            "• Password protection adds access control only\n"
            "• Future updates will implement AES encryption\n"
            "• Use appropriate discretion with sensitive information"
        ),
        inline=False
    )

    embed.set_footer(text="🕵️ For technical support or concerns, contact the Agent's operator.")

    await interaction.response.send_message(embed=embed)

@client.event
async def on_ready():
    await tree.sync()
    print("Logged in and Ready!")

@client.event
async def on_guild_join(guild):
    log_channel = client.get_channel(updatesCH)
    if log_channel:
        ownerID = guild.owner_id
        owner = await client.fetch_user(ownerID)
        embed = discord.Embed(
            title="📥 Bot Added to a Server",
            description=f"The bot has been added to a new server!",
            color=discord.Color.green()
        )
        embed.add_field(name="Guild Name", value=guild.name, inline=False)
        embed.add_field(name="Guild ID", value=guild.id, inline=False)
        embed.add_field(name="Owner", value=f"{owner} ({ownerID})", inline=False)
        embed.add_field(name="Member Count", value=guild.member_count, inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.set_footer(text="📆")
        embed.timestamp = discord.utils.utcnow()
        await log_channel.send(embed=embed)

@client.event
async def on_guild_remove(guild):
    log_channel = client.get_channel(updatesCH)
    if log_channel:
        ownerID = guild.owner_id
        owner = await client.fetch_user(ownerID)
        embed = discord.Embed(
            title="📤 Bot Removed from a Server",
            description=f"The bot has been removed from a server.",
            color=discord.Color.red()
        )
        embed.add_field(name="Guild Name", value=guild.name, inline=False)
        embed.add_field(name="Guild ID", value=guild.id, inline=False)
        embed.add_field(name="Owner", value=f"{owner} ({ownerID})", inline=False)
        embed.add_field(name="Member Count", value=guild.member_count, inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.set_footer(text="📆")
        embed.timestamp = discord.utils.utcnow()
        await log_channel.send(embed=embed)

def run_bot():
    client.run(token)

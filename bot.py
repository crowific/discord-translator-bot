import os
import asyncio
import discord
from googletrans import Translator

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is missing")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
translator = Translator()

CHANNELS = {
    "en": 1488204114843275304,  # leadership-group (English)
    "es": 1493371326298325092,  # Spanish
    "fr": 1493374866437705728,  # French
    "pt": 1493433598814978208,  # Portuguese
    "ar": 1493433830584090675,  # Arabic
}

LANGUAGE_INFO = {
    "en": {"label": "English", "emoji": "🇺🇸"},
    "es": {"label": "Spanish", "emoji": "🇪🇸"},
    "fr": {"label": "French", "emoji": "🇫🇷"},
    "pt": {"label": "Portuguese", "emoji": "🇵🇹"},
    "ar": {"label": "Arabic", "emoji": "🇸🇦"},
}


def get_language_from_channel(channel_id: int):
    for lang_code, mapped_channel_id in CHANNELS.items():
        if mapped_channel_id == channel_id:
            return lang_code
    return None


def translate_text_sync(text: str, src_lang: str, dest_lang: str) -> str:
    translated = translator.translate(text, src=src_lang, dest=dest_lang).text
    if dest_lang == "ar":
        return "\u200F" + translated
    return translated


async def translate_text(text: str, src_lang: str, dest_lang: str) -> str:
    return await asyncio.to_thread(translate_text_sync, text, src_lang, dest_lang)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    source_lang = get_language_from_channel(message.channel.id)
    if source_lang is None:
        return

    text = message.content.strip()
    if not text:
        return

    username = message.author.display_name
    source_info = LANGUAGE_INFO[source_lang]

    try:
        target_langs = [lang for lang in CHANNELS if lang != source_lang]

        translation_tasks = [
            translate_text(text, source_lang, dest_lang)
            for dest_lang in target_langs
        ]

        translated_results = await asyncio.gather(*translation_tasks, return_exceptions=True)

        for dest_lang, translated_text_result in zip(target_langs, translated_results):
            if isinstance(translated_text_result, Exception):
                print(f"Translation failed for {dest_lang}: {translated_text_result}")
                continue

            channel = client.get_channel(CHANNELS[dest_lang])
            if channel is None:
                print(f"Could not find channel for {dest_lang}: {CHANNELS[dest_lang]}")
                continue

            dest_info = LANGUAGE_INFO[dest_lang]

            formatted_message = (
                f"**{username}**\n"
                f"*From {source_info['emoji']} {source_info['label']} → {dest_info['emoji']} {dest_info['label']}*\n"
                f"{translated_text_result}"
            )

            await channel.send(formatted_message)

    except Exception as e:
        print("Error:", e)


client.run(TOKEN)

import json
import re
import urllib.request
from typing import List

import discord
import pandas as pd
from bs4 import BeautifulSoup
from discord.ext import commands, tasks

with open('config.json') as f:
    config = json.loads(f.read())

# load the last recorded tag, if it exists.
try:
    with open("last_recorded_tag.txt", 'r') as f:
        last_tag = f.read()
except FileNotFoundError:
    last_tag = None

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)
url_stub = 'https://hvzrit.club'

def get_vs_players():
    url = r'https://hvzrit.club/'
    with urllib.request.urlopen(url) as f:
        a = f.read().decode('utf-8')
    parsed_html = BeautifulSoup(a, features='lxml')
    humans = parsed_html.body.find('div', attrs={'id':'humancount-container'}).text
    h = re.sub("[^0-9]", "", humans)
    zombies = parsed_html.body.find('div', attrs={'id':'zombiecount-container'}).text
    z = re.sub("[^0-9]", "", zombies)
    return h, z

def get_tags() -> List:
    url = r'https://hvzrit.club/tags/'
    tables = pd.read_html(url, extract_links="all")  # Returns list of all tables on page
    table_0 = tables[0]
    return table_0.values

def make_tag_embed(tag):
    """Makes an embed for the tag """
    e = discord.Embed(color=discord.Color.green(), title=f"{tag[1][0]} was tagged by {tag[0][0]}")
    e.add_field(name='Timestamp:', value=tag[2][0])
    return e

def format_txt(t):
    """Formats tags into a consistent format"""
    return f"[{t[1][0]}]({url_stub}{t[1][1]}) was tagged by [{t[0][0]}]({url_stub}{t[0][1]}) at {t[2][0]}"

def get_new_tags_only():
    """Gets new tags that haven't been sent, then saves the new last tag. """
    global last_tag
    t = get_tags()
    if last_tag is None:
        # If there's no last tag, just return all of them and then set it to the last one
        last_tag = format_txt(t[0])
        save_last()
        return t
    tags_to_return = []
    # loop through all tags in order of sooner first, so when you get to the
    # one you know you stop and return all the ones you already have
    for tag in t:
        if format_txt(tag) == last_tag:
            last_tag = format_txt(t[0])
            save_last()
            return tags_to_return
        tags_to_return.append(tag)
    # if you didn't find the one you were looking for, something is probably wrong, so just return the most recent one,
    # and save it so this doesn't happen again
    last_tag = format_txt(t[0])
    save_last()
    return [t[0]]

def save_last():
    """Just saves the last tag to file, yes it's a bit hacky but it works for a simple bot"""
    with open("last_recorded_tag.txt", 'w') as f:
        f.write(last_tag)

# @bot.command()
# async def tags(ctx):
#     """Manually triggered get new tags"""
#     await check_new_tags()

@tasks.loop(seconds=config['check_interval'])
async def check_new_tags():
    """Checks for new tags, then sends them in the order they happened to all configured channels"""
    print("Checking for new tags!")
    tags = get_new_tags_only()
    if len(tags)==0:
        print("No new tags")
        return
    for t in tags[::-1]:
        embed = make_tag_embed(t)
        for channel in config['channels']:
            ch = bot.get_channel(channel)
            if ch is None:
                ch = await bot.fetch_channel(channel)
            await ch.send(embed=embed)

@tasks.loop(seconds=60)
async def status():
    """Sets bot status to the current number of humans and zombies"""
    h, z = get_vs_players()
    await bot.change_presence(activity=discord.CustomActivity(name=f'{h}🧍 vs {z}🧟'))

@bot.event
async def on_ready():
    check_new_tags.start()
    status.start()

bot.run(config['token'])
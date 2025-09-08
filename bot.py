import json
import re
import shutil
import urllib.request
from typing import List

import discord
import pandas as pd
from bs4 import BeautifulSoup
from discord.ext import commands, tasks

try:
    with open('config.json') as f:
        config = json.loads(f.read())
except FileNotFoundError:
    shutil.copyfile('config.example.json', 'config.json')
    exit("created config.json, please fill this in with your own values")

base_url = config['base_url']

# load the last recorded tag, if it exists.
try:
    with open("last_recorded_tag.txt", 'r') as f:
        last_tag = f.read()
except FileNotFoundError:
    last_tag = None

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['prefix'], intents=intents)


def get_vs_players():
    """Get the number of players on each side"""
    with urllib.request.urlopen(base_url) as f:
        a = f.read().decode('utf-8')
    parsed_html = BeautifulSoup(a, features='lxml')
    humans = parsed_html.body.find('div', attrs={'id':'humancount-container'}).text
    h = re.sub("[^0-9]", "", humans)
    zombies = parsed_html.body.find('div', attrs={'id':'zombiecount-container'}).text
    z = re.sub("[^0-9]", "", zombies)
    return h, z

def get_tags() -> List:
    """Rip the tags from the table on the hvz website"""
    url = f'{base_url}/tags/'
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
    return f"[{t[1][0]}]({base_url}{t[1][1]}) was tagged by [{t[0][0]}]({base_url}{t[0][1]}) at {t[2][0]}"

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


@bot.command(name='leaderboard', aliases=['lb'])
async def leaderboard(ctx):
    """Display the leaderboard of zombies with the most tags."""
    leaderboard_limit = 10
    uri = f"""{base_url}/api/datatables/players?draw=2&columns%5B0%5D%5Bdata%5D=pic&columns%5B0%5D%5Bname%5D=picture&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=name&columns%5B1%5D%5Bname%5D=name&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=status&columns%5B2%5D%5Bname%5D=status&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=tags&columns%5B3%5D%5Bname%5D=tags&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=clan&columns%5B4%5D%5Bname%5D=clan&columns%5B4%5D%5Bsearchable%5D=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=1&order%5B0%5D%5Bdir%5D=asc&start=0&length=1000&search%5Bvalue%5D=&search%5Bregex%5D=false&_=1757339698811"""
    with urllib.request.urlopen(uri) as f:
        a = f.read().decode('utf-8')
        j = json.loads(a)

    players = j['data']
    zombies = []
    humans = []
    for player in players:
        if player["DT_RowClass"] == "dt_human":
            humans.append(player)
        elif player["DT_RowClass"] == "dt_zombie":
            zombies.append(player)

    sorted_zombies = sorted(zombies, key=lambda d: d['tags'], reverse=True)
    if len(sorted_zombies) == 0:
        await ctx.send("There are no zombies!")
        return
    leaderboard_message_text = """Leaderboard: \n"""
    i = 1
    for zombie in sorted_zombies[0:leaderboard_limit]:
        player_name = BeautifulSoup(zombie["name"], features="lxml").text[:-1]
        leaderboard_message_text += f"#{i} - [{player_name}]({base_url+zombie["DT_RowData"]["person_url"]}) - {zombie["tags"]}\n"
        i+=1
    await ctx.send(leaderboard_message_text)

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
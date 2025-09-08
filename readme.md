# HvZBot

This is a discord bot designed to put the tag feed into a discord channel, as well as whatever other features I think of. 

## Setup:

The author of this code decided to use [uv](https://docs.astral.sh/uv/), because it was incredibly painless to setup. Thus, to setup, after installing uv, you should only need to do one thing. 
```
uv run python bot.py
```

The first time you run this, it will exit immediately, having created `config.json` in the run directory. You should then be able to fill in the values in the configuration file, with `token` being the discord token gotten from [the discord developer portal](https://discord.com/developers/applications), and `channels` being a list of channel ids in which to send the tag-feed (All others have sane defaults). 

After having completed this setup, you should be able to run the bot like normal with the same `uv run python bot.py`. 


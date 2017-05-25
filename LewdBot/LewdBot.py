import discord
import aiohttp
import asyncio
import praw
import os
import sys
import json

CHANNEL_ID_LEWD = 'chan1id'
CHANNEL_ID_TESTING = 'chan2id'
DEFAULT_CHANNEL_LEWD = None
MONITORED_SUBS_FILE = 'monitoredSubs'
TOP_LEWDS_FILE = 'topLewds'
POST_INTERVAL = 60 * 60 * 12
MAX_LEWDS_PER_UPDATE = 5

client = discord.Client()

reddit = praw.Reddit(client_id='id',
                     client_secret='secret',
                     user_agent='discord:LewdBot:1.0')

subreddits = []
if os.path.exists(MONITORED_SUBS_FILE):
    with open(MONITORED_SUBS_FILE) as file:
        subreddits = json.load(file)

currentTopPosts = None
if os.path.exists(TOP_LEWDS_FILE):
    with open(TOP_LEWDS_FILE) as file:
        currentTopPosts = json.load(file)

channelsUpdating = []

@client.event
async def on_ready():
    print('Logged in as {}, client id: {}'.format(client.user.name, client.user.id))
    print(client)

@client.event
async def on_message(message):
    global currentTopPosts
    if message.channel.id == CHANNEL_ID_LEWD or message.channel.id == CHANNEL_ID_TESTING:
        if message.content.startswith('!lewds'):
            if len(subreddits) > 0:
                topPosts = [listgen.next() for listgen in [reddit.subreddit(sub).top('day', limit=1) for sub in subreddits]]
                newTopPosts = {post.id: {'title': post.title, 'url': post.url, 'subreddit': post.subreddit_name_prefixed} for post in topPosts}
                newTopPostsDiff = newTopPosts.keys()
                if currentTopPosts:
                    newTopPostsDiff = newTopPosts.keys() - currentTopPosts.keys()
                currentTopPosts = newTopPosts
                for count, postId in enumerate(newTopPostsDiff):
                    if count < MAX_LEWDS_PER_UPDATE:
                        await sendMessage(channel, '{} {} {}'.format(newTopPosts[postId]['subreddit'], newTopPosts[postId]['title'], newTopPosts[postId]['url']))
            else:
                await sendMessage(message.channel, 'LewdBot is not monitoring any subreddits for lewds', 5)
            saveAll()
        elif message.content.startswith('!subs'):
            await sendMessage(message.channel, 'LewdBot is currently monitoring these subreddits: {}'.format(['/r/{}'.format(sub) for sub in subreddits]), 5)
        elif message.content.startswith('!addsub') or message.content.startswith('!addsubs'):
            newSubs = message.content.split()[1:]
            newSubs = [newSub.replace('/r/', '') for newSub in newSubs]
            for newSub in newSubs:
                if newSub not in subreddits:
                    subreddits.append(newSub)
                    await sendMessage(message.channel, 'LewdBot is now monitoring /r/{}'.format(newSub), 5)
        elif message.content.startswith('!removesub') or message.content.startswith('!removesubs'):
            delSubs = message.content.split()[1:]
            delSubs = [delSub.replace('/r/', '') for delSub in delSubs]
            for delSub in delSubs:
                if delSub in subreddits:
                    subreddits.remove(delSub)
                    await sendMessage(message.channel, 'LewdBot is no longer monitoring /r/{}'.format(delSub), 5)
        elif message.content.startswith('!clearsubs'):
            subreddits.clear()
            currentTopPosts = None
            await sendMessage(message.channel, 'LewdBot is no longer monitoring any subreddits for lewds', 5)
        elif message.content.startswith('!startlewds'):
            if message.channel not in channelsUpdating:
                channelsUpdating.append(message.channel)
                await sendMessage(message.channel, 'LewdBot is now publishing T O P L E W D S'.format(len(subreddits)), 5)
                await updateLewds(message.channel)
        elif message.content.startswith('!stoplewds'):
            if message.channel in channelsUpdating:
                channelsUpdating.remove(message.channel)
                await sendMessage(message.channel, 'LewdBot is no longer publishing lewds'.format(len(subreddits)), 5)
        elif message.content.startswith('!savesubs'):
            saveAll()
            await sendMessage(message.channel, 'LewdBot saved {} monitored subreddits'.format(len(subreddits)), 5)

def saveAll():
    with open(MONITORED_SUBS_FILE, 'w') as file:
        json.dump(subreddits, file)
    with open(TOP_LEWDS_FILE, 'w') as file:
        json.dump(currentTopPosts, file)

async def sendMessage(channel, contents, deleteAfter=0):
    msg = await client.send_message(channel, contents)
    if channel.id == CHANNEL_ID_TESTING:
        deleteAfter = 5
    if deleteAfter > 0:
        await asyncio.sleep(min(deleteAfter, 30))
        await client.delete_message(msg)

async def updateLewds(channel):
    global currentTopPosts
    if channel in channelsUpdating:
        if len(subreddits) > 0:
            topPosts = [listgen.next() for listgen in [reddit.subreddit(sub).top('day', limit=1) for sub in subreddits]]
            newTopPosts = {post.id: {'title': post.title, 'url': post.url, 'subreddit': post.subreddit_name_prefixed} for post in topPosts}
            newTopPostsDiff = newTopPosts.keys()
            if currentTopPosts:
                newTopPostsDiff = newTopPosts.keys() - currentTopPosts.keys()
            currentTopPosts = newTopPosts
            for count, postId in enumerate(newTopPostsDiff):
                if count < MAX_LEWDS_PER_UPDATE:
                    await sendMessage(channel, '{} {} {}'.format(newTopPosts[postId]['subreddit'], newTopPosts[postId]['title'], newTopPosts[postId]['url']))
            saveAll()
        await asyncio.sleep(POST_INTERVAL)
        await updateLewds(channel)

client.run('token')
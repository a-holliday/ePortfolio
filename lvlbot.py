import discord
from discord.ext import commands
import datetime, time
import json
import sqlite3
import math
client = commands.Bot(command_prefix='/')

@client.event
async def on_ready(): #code that is issued on the start up of the bot
    db = sqlite3.connect('users.sqlite') # connect to a databaase called users
    cursor = db.cursor() #cursor is used to manipulate data in db
    #create table if not already existing with username, exp, lvl, hourly_count and thanks_count and cookies
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
        username UNSIGNED BIGINT,
        experience UNSIGNED BIGINT,
        level UNSIGNED SMALLINT,
        hourly_count TIMESTAMP,
        thanks_count SMALLINT,
        cookies UNSIGNED BIGINT
        )
    ''')
    print("I am online")
    cursor.close()
    db.close()




@client.event
async def on_message(message): #every message is checked for a bot command or entered for exp points
    if (message.author.bot): #if message issued by bot then ignore message
        return
    db = sqlite3.connect('users.sqlite') #connect database to users.sqlite
    cursor = db.cursor() #attach cursor to previously connected database
    cursor.execute(f"SELECT username FROM users where username = {message.author.id}" )
    result = cursor.fetchone()
    if result is None:
        await new_user(message.author.id)
    
    await add_exp(message.author.id, 5)
    await level_up(message.author.id, message)
    await client.process_commands(message) #sends the message forward so commands can be processed


async def new_user(user): #initalizes for new user the values
    db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
    cursor = db.cursor()  # attach cursor to previously connected database
    sql = ("INSERT INTO users(username, experience, level, hourly_count, thanks_count, cookies) VALUES(?,?,?,?,?,?)")
    values = ((user), 0, 1, datetime.datetime.now(), 3, 0) #inital values
    cursor.execute(sql,values)
    db.commit()
    
async def add_exp(user, exp): #adds experience points
    db = sqlite3.connect('users.sqlite') #connect database to users.sqlite
    cursor = db.cursor() #attach cursor to connected database
    cursor.execute(f"SELECT experience FROM users WHERE username = {user}")
    result = cursor.fetchone()
    new_exp = exp + (int)(result[0]) # result needs to specify the index becaus cursor returns tuple
    cursor.execute(f"UPDATE users SET experience = {new_exp} WHERE username = {user}")
    db.commit()

async def level_up(user , message): #if critera met levels up user
    db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
    cursor = db.cursor()  # attach cursor to connected database
    cursor.execute(f"SELECT experience FROM users WHERE username = {user}")
    exp = cursor.fetchone()
    cursor.execute(f"SELECT level FROM users WHERE username = {user}")
    lvl_start = cursor.fetchone() #returns a tuple with one index
    lvl_start = lvl_start[0]  #specify the index of the tuple we need
    lvl_end = int(exp[0] ** (1 / 4))
    if lvl_start < lvl_end:
        await message.channel.send(f'{client.get_user(user).mention} has leveled up to level {lvl_end}')
        cursor.execute(f"UPDATE users SET level = {lvl_end} WHERE username = {user}")
        db.commit()

async def add_cookie(user): #adds a cookie to the database for specified user
    db = sqlite3.connect('users.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT cookies FROM users WHERE username = {user}")
    result = cursor.fetchone()
    new_cookies = 1 + (int)(result[0])  # result needs to specify the index becaus cursor returns tuple
    cursor.execute(f"UPDATE users SET cookies = {new_cookies} WHERE username = {user}")
    db.commit()

async def countdown(ctx, user): #cooldown for number of thanks that be recieved
    db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
    cursor = db.cursor()  # attach cursor to connected database
    cursor.execute(f"SELECT hourly_count FROM users WHERE username = {user}") #get the timestamp from database
    timestamp = cursor.fetchone()
    print(timestamp)
    print(type(timestamp[0]))
    elapsed_time = datetime.datetime.now() - datetime.datetime.strptime(timestamp[0], "%Y-%m-%d %H:%M:%S.%f") #check to see if an hour has passed
    print(elapsed_time.total_seconds())
    if elapsed_time.total_seconds() > 3600: #if an hour has passed, set current time to time stamp and refresh thanks_count to 3
        print(elapsed_time)
        cursor.execute(f"UPDATE users SET thanks_count = '{3}' WHERE username = '{user}'")
        cursor.execute(f"UPDATE users SET hourly_count = '{datetime.datetime.now()}' WHERE username = '{user}'")
        db.commit()
    cursor.execute(f"SELECT thanks_count FROM users WHERE username = '{user}'")
    thanks_count = cursor.fetchone();
    if thanks_count[0] > 0:
        thanks_count_non_tuple = thanks_count[0] - 1 # transfer tuple amount to non tuple variable to modify it
        print(thanks_count_non_tuple)
        cursor.execute(f"UPDATE users SET thanks_count = '{thanks_count_non_tuple}' WHERE username = '{user}'")
        db.commit()
        return True
    elif ( thanks_count[0] == 0 and elapsed_time.total_seconds() < 3600):
        seconds = int(3600 - elapsed_time.total_seconds())
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60

        await ctx.message.channel.send(
            f"Sorry,{client.get_user(user).mention} you have to wait {hour:02d} hour(s),  {minutes:02d} minute(s) and {seconds:02d} second(s) to be thanked")
        return False


@client.command(aliases =["thank"])
async def thanks(ctx, member: discord.Member): #command that gives cookie to user an indicator of helpfulness
    if ctx.author == member:
        await ctx.message.channel.send("You can always thank yourself, but it won't get you cookies")
        return
    else:
        db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
        cursor = db.cursor()  # attach cursor to connected database
        cursor.execute(f"SELECT username FROM users where username = {member.id}")
        result = cursor.fetchone()
        if result is None:
            await new_user(member.id)
        if await countdown(ctx, member.id):
            await add_cookie(member.id)
            await ctx.channel.send(f"Cool {member.mention} got a cookie for that. 🍪")





@client.command()
async def leaderboard(ctx): #command that displays top ten users with highest experience points
    embed = discord.Embed(title="Leaderboard")
    db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
    cursor = db.cursor()  # attach cursor to connected database
    cursor.execute("SELECT username, level, experience FROM users ORDER BY experience DESC LIMIT 10");
    results = cursor.fetchall()
    print(results)


    count = 1
    embed.set_thumbnail(url=client.get_user(results[0][0]).avatar_url)

    for user in results:

        embed.add_field(name="Rank", value=count, inline=True)

        embed.add_field(name="Name", value=client.get_user(int(user[0])).name, inline=True)

        embed.add_field(name="Level ", value= user[1], inline=True)

        #await ctx.channel.send(f"{count}. {user[0]} level: {user[1]}")

        count +=1
    await ctx.channel.send(embed=embed)


@client.command()
async def cookieboard(ctx): #command that displays top ten leaders for numbers of cookies
    embed2 = discord.Embed(title="Cookieboard")
    db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
    cursor = db.cursor()  # attach cursor to connected database
    cursor.execute("SELECT username, cookies FROM users ORDER BY cookies DESC LIMIT 10");
    results = cursor.fetchall()
    print(results)
    count = 1
    embed2.set_thumbnail(url=client.get_user(results[0][0]).avatar_url)

    for user in results:
        #await ctx.channel.send(f"{count}. {client.get_user(user[0]).name} cookie(s)🍪: {user[1]}")

        embed2.add_field(name="Rank", value=count, inline=True)

        embed2.add_field(name="Name", value=client.get_user(int(user[0])).name, inline=True)

        embed2.add_field(name="Cookies 🍪 ", value=user[1], inline=True)
        count +=1
    await ctx.channel.send(embed=embed2)

@client.command(aliases =["cookierank"])
async def cookie_rank(ctx): #command that gives rank on cookies
    db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
    cursor = db.cursor()  # attach cursor to connected database
    cursor.execute("SELECT username, cookies  FROM users ORDER BY cookies DESC");
    results = cursor.fetchall()
    print(results)
    count = 1
    print(type(ctx.author))
    print(type(results[1][0]))
    print(results[1][0] == ctx.author)
    for user in results:
        if user[0] == str(ctx.author):
            await ctx.channel.send(f'Your rank is {count} on the  cookie leaderboard 🍪')
            return
        count += 1



@client.command()
async def rank(ctx): #command that gives rank on experience leaderboard
    db = sqlite3.connect('users.sqlite')  # connect database to users.sqlite
    cursor = db.cursor()  # attach cursor to connected database
    cursor.execute("SELECT username  FROM users ORDER BY experience DESC");
    results = cursor.fetchall()
    count = 1
    for user in results:
        print(user[0])
        if user[0] == ctx.author.id:
            await ctx.channel.send(f'Your rank is number {count} on the experience leaderboard')
        count+= 1



client.run("token removed for security")


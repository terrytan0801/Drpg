

import discord
import dotenv
import os
import time
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import re
import time
import webserver

dotenv.load_dotenv()
uri = os.getenv("mongodb_uri")
token = os.getenv('neon_server_token')
dev_id = os.getenv("Neon_dev_server")
dev_person = int(os.getenv("terry_id"))

client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

#add collection into database
db = client.neon1
collection = db.members


from discord.ext import commands
from discord import app_commands

now = time.strftime("%Y-%m-%d %H:%M:%S")


class Client(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.voice_time = {}


    async def on_ready(self):
    
        user =await self.fetch_user(dev_person)
        print('welcome ' + str(user))
        print(f"Discord bot is ready !!! welcome {self.user}")
        try:
            #clear duplicate command and try to sync command once again to the server

            # self.tree.clear_commands(guild=None)   # 清 global
            # self.tree.clear_commands( )  # 清 guild

            # ❗ 把你代码里的 command 重新加回 guild

            synced_command =  await self.tree.sync()
            print('-----------------')
            print(f"Synced Command : {len(synced_command)}")
            print('-----------------')
            for cmd in synced_command:
                print(f"Name: {cmd.name} | Description: {cmd.description}")
            print('-----------------')
            print("Synced Server  ")
            print('=================')
            for guild in self.guilds:
                print(guild.name)
                
        except Exception as e:
                print(e)

        for guild in self.guilds:
                for vc in guild.voice_channels:
                    for member in vc.members:
                        if not member.bot:
                            # 假设他们现在才刚被记录，时间从 bot 启动算起
                            self.voice_time[member.id] = time.time()
                            print(f"{member.name} is already in {vc.name}, start tracking voice XP and gold gain.")

        embed = discord.Embed(title="Neon Server Bot On ⭐" ,url="https://www.instagram.com/terrytan0801/?hl=en", description=f"*** System connect at {now} ***" )
        for guild in self.guilds:
            all_member = [i for i in guild.members if i.bot == False]
            embed.add_field(name=f"Server : {guild.name}", value=f"Total Member : {len(all_member)}" , inline=False)
            Neon_logo = discord.File(r"assets\n_logo.png",filename="Neon_logo.png")
            embed.set_thumbnail(url="attachment://Neon_logo.png")
            
            for member in all_member:
                level_start = 1
                collection.update_one(
                                        {"_id": member.id},
                                        {"$set": {"name": member.name },
                                        "$addToSet": {"servers": guild.name},  # 自动加入服务器名，避免重复
                                        "$setOnInsert": {
                                                    "level": level_start,
                                                    "xp": 0,
                                                    "to_next_level": level_start * 1000 * 1.2  # level*1000 +20%
                                        }},
                                        upsert=True  
                                    )
                #change user nickname to show level
                db_user = collection.find_one({"_id": member.id})
                level = db_user.get("level", 1)
                try:
                    base_name = re.sub(r"\s*\[Lv\.\d+\]", "", member.display_name)
                    new_nick = f"{base_name} [Lv.{level}]"
                    await member.edit(nick=new_nick)
                except Exception as e:
                    pass

                

            
        for guild in self.guilds:
            if guild.id == dev_id :
                if guild.system_channel:
                    try:
                        await user.send(embed=embed,file=Neon_logo)
                    except Exception as e:
                        print(e)
        
    def check_level(self,member_id):
                user = collection.find_one({"_id": member_id})
                if not user:
                    return
                
                current_lvl = user.get("level",1)
                current_xp = user.get("xp",0)
                leveled_up = False

                while current_xp >= current_lvl * 1000 * 1.2:
                    current_xp -= current_lvl * 1000 * 1.2
                    current_lvl += 1
                    leveled_up = True
                
                if leveled_up:
                    collection.update_one(
                        {"_id": member_id},
                        {"$set": {"level": current_lvl, "xp": current_xp, "to_next_level": current_lvl * 1000 * 1.2}}
                    )
                    return current_lvl
                return None
    


    async def on_message(self,msg):

        xp_gain = 10
        gold_gain = 0.15
 
        if msg.author == self.user:
            return
        user_data = collection.find_one({"_id": msg.author.id}) or {}
        gold = user_data.get("gold", 0)
        xp = user_data.get("xp", 0)
        level = user_data.get("level", 1)
        print(f'Server : {msg.guild} \nChannel : {msg.channel}  \nAuthor : {msg.author} \nContent : {msg.content},\nGold : {gold}\nXP : {xp}\nLevel : {level}')

        if msg.attachments:
            for file in msg.attachments:
                print(f"Server : {msg.guild} \nChannel : {msg.channel}  \nAuthor : {msg.author} \nFilename : {file.filename}")
        
        collection.update_one({"_id": msg.author.id}, {"$inc": {"xp": xp_gain , "gold": gold_gain}},upsert=True)
        new_level = self.check_level(msg.author.id)
        if new_level:
            await msg.channel.send(f"🎉 {msg.author.mention} has leveled up! Now Level {new_level}!")


        
        
    async def on_member_join(self,member):
        level_start = 1
        collection.update_one( {"_id": member.id},
        {"$setOnInsert": {
            "name": member.name,
            "level": level_start,
            "xp": 0,
            "gold": 1,
            "to_next_level": level_start * 1000 * 1.2,
            "servers": [member.guild.name]
        }},
        upsert=True)

        for guild in self.guilds:
            if guild.id == dev_id :
                if guild.system_channel:
                    try:
                        embed = discord.Embed(title="Welcome to Neon Server !!!" , description=f"*** Welcome {member.mention} to Neon Server !!! ***" )
                        embed.set_author(name=member.name, icon_url=member.avatar.url)

                        await guild.system_channel.send(embed=embed , view=Character())
                    except Exception as e:
                        print(e)

    async def on_voice_state_update(self, member, before, after):

        # ❌ 忽略 bot
        if member.bot:
            return
        
        db_user_id = member.id
        # 🎧 加入语音
        if before.channel is None and after.channel is not None:
            self.voice_time[db_user_id] = time.time()
            print(f"{member.name} joined voice channel: {after.channel.name}")

        # 🚪 离开语音
        elif before.channel is not None and after.channel is None:
            start_time = self.voice_time.pop(db_user_id,None)
            if start_time:
                duration = time.time() - start_time
                minutes = int(duration // 60)
                xp_gain = minutes * 1.5
                gold_gain = minutes * 0.1

                print(f"{member.name} stayed {minutes} min → +{xp_gain} XP")
            else:
                xp_gain = 0 
                gold_gain = 0

            if xp_gain > 0:
                collection.update_one(
                    {"_id": db_user_id},
                    {"$inc": {"xp": xp_gain, "gold": gold_gain}},
                    upsert=True
                )
            
                new_level = self.check_level(db_user_id)

                if new_level and member.guild.system_channel:
                    await member.guild.system_channel.send(
                        f"🎉 {member.mention} leveled up to {new_level} from voice!"
                        )

            print(f"{member.name} left voice channel: {before.channel.name}")

        # 🔁 切换频道（加一个保护）
        elif before.channel != after.channel and before.channel and after.channel:
            print(f"{member.name} switched from {before.channel.name} to {after.channel.name}")
            start_time = self.voice_time.pop(db_user_id, None)
            if start_time:
                duration = time.time() - start_time
                minutes = int(duration // 60)
                xp_gain = minutes * 1.5
                gold_gain = minutes * 0.1
                print(f"{member.name} stayed {minutes} min \n→ +{xp_gain} XP\n+{gold_gain} Gold")

                if xp_gain > 0:
                    collection.update_one(
                        {"_id": db_user_id},
                        {"$inc": {"xp": xp_gain, "gold": gold_gain}},
                        upsert=True
                    )
                    new_level = self.check_level(db_user_id)
                    if new_level and member.guild.system_channel:
                        await member.guild.system_channel.send(
                            f"🎉 {member.mention} leveled up to {new_level} from voice!"
                        )

            # 然后记录新频道进入时间
            self.voice_time[db_user_id] = time.time()



intent = discord.Intents.default()
intent.members =True
intent.message_content = True
intent.voice_states = True
neon = Client(command_prefix='!', intents=intent)

class Character(discord.ui.View):
    async def assign_role(self, interaction, button, role_name):
        # 所有职业列表
        all_roles = ["Warrior", "Mage", "Archer"]

        # 先获取用户已有角色
        user_roles = [r.name for r in interaction.user.roles]

        # 移除用户其他职业
        for r in all_roles:
            if r in user_roles and r != role_name:
                role_obj = discord.utils.get(interaction.guild.roles, name=r)
                if role_obj:
                    await interaction.user.remove_roles(role_obj)

        # 获取当前角色
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role is None:
            role = await interaction.guild.create_role(name=role_name)

        # 添加新角色
        await interaction.user.add_roles(role)

        # 第一次响应
        await interaction.response.send_message(f"You chose {role_name}", ephemeral=True)

        # disable其他按钮
        for item in self.children:
            if item != button:
                item.disabled = True

        # 编辑 message
        await interaction.message.edit(
            content=f"You picked {role_name}",
            view=self
        )

    @discord.ui.button(label="Warrior", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def get_warrior(self, interaction, button):
        await self.assign_role(interaction, button, "Warrior")

    @discord.ui.button(label="Mage", style=discord.ButtonStyle.blurple, emoji="🔮")
    async def get_mage(self, interaction, button):
        await self.assign_role(interaction, button, "Mage")

    @discord.ui.button(label="Archer", style=discord.ButtonStyle.green, emoji="🏹")
    async def get_archer(self, interaction, button):
        await self.assign_role(interaction, button, "Archer")
        
develop_server = neon.get_guild(dev_id)

@neon.tree.command(name="character", description="Choose your character" ,  )
async def character(interaction: discord.Interaction):
    view = Character()
    await interaction.response.send_message("Choose your character:", view=view , ephemeral=True)

@neon.tree.command(name="check_role",description="check server available roles" ,  )
async def check_role(interaction:discord.Interaction):
    server = interaction.guild
    role_list = [i.name for i in server.roles] 
    await interaction.response.send_message(f"Available roles: {', '.join(role_list)}", ephemeral=True)

@neon.tree.command(name='clear_role',description="clear all role in server" ,  )
async def clear_role(interaction:discord.Interaction):
    server = interaction.guild
    for role in server.roles:
        if role.name != "@everyone":
            try:
                await role.delete()
                print(f"Deleted role: {role.name}")
            except Exception as e:
                print(f"Failed to delete role: {role.name} - {e}")

@neon.tree.command(name="ping", description="Check the bot's latency", )
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! Latency: {round(neon.latency * 1000)} ms" , ephemeral=True)


@neon.tree.command(name = "help" , description="Show every description of command" , )    
async def help(interaction :discord.Interaction):
    embed = discord.Embed(title="Help Command List" , description="Here are all the available commands and their descriptions:")
    for cmd in neon.tree.get_commands():
        embed.add_field(name=cmd.name, value=cmd.description, inline=False)
    await interaction.response.send_message(embed=embed , ephemeral=True)

@neon.tree.command(name="rank", description="Pop out a window for certain rank",  )
async def rank(interaction:discord.Interaction):
    # Implementation for the rank command
    top10 = collection.find({"servers": {"$in": [interaction.guild.name]}}).sort("level", -1).limit(10)
    embed = discord.Embed(title="Server Ranking", description="Top 10 members by Level", color=discord.Color.blue())
    for i in top10:
        embed.add_field(name=i.get("name"), value=i.get("level"), inline=False)

    await interaction.response.send_message(embed=embed) 
    #
@neon.tree.command(name="check_level", description="Check your level and XP",  )
async def check_self_level(interaction:discord.Interaction):
    user_id = interaction.user.id
    guild_name = interaction.guild.name
    member_data = collection.find_one({"_id": user_id, "servers": {"$in": [guild_name]}})
    if member_data:
        xp = member_data.get("xp", 0)
        level = member_data.get("level", 0)
        embed = discord.Embed(title="Your Level and XP", color=discord.Color.green())
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="XP", value=xp, inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(f"{interaction.user.mention}, you have no XP or level data yet.", ephemeral=True)

webserver.keep_alive()
neon.run(token)
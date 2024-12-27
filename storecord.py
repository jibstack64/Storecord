
# Include required libraries
import discord
import tkinter
import threading
import requests
import asyncio
import os, sys
import atexit
import json
import math
import time
import webbrowser
from tkinter import simpledialog
from tkinter import filedialog
from tkinter import messagebox

DB_FILE =       "database.json"
CONFIG_FILE =   "config.txt"
TOKEN =         None
CHANNEL_ID =    None
MAX_FILESIZE =  10000000 # 10MB (set by Discord)

try:
    with open(CONFIG_FILE, "r") as f:
        TOKEN, CHANNEL_ID = f.readlines()
except FileNotFoundError:
    pass

if TOKEN == None:
    root = tkinter.Tk()
    root.withdraw()
    TOKEN = simpledialog.askstring("Token entry", "Bot token:")
    CHANNEL_ID = simpledialog.askstring("Channel ID entry", "Channel ID:")
    with open(CONFIG_FILE, "w") as f:
        f.write(f"{TOKEN}\n{CHANNEL_ID}")
    root.quit()

# Setup database

try:
    database = json.load(open(DB_FILE))
except FileNotFoundError:
    database = {}

atexit.register(lambda : json.dump(database, open(DB_FILE, "w"), indent=4))

# Discord bot code

class Client(discord.Client):
    
    channel: discord.TextChannel = None

    async def upload(self, filename: str, parts: list[bytes]):
        temp_file = f"tmp-{filename}"
        for i in range(len(parts)):
            with open(temp_file, "wb") as f:
                f.write(parts[i])

            message = await self.channel.send(
                file = discord.File(temp_file, f"{filename}{('-' + str(i)) if i > 0 else ''}")
            )
            parts[i] = message.attachments[0].url
            os.remove(temp_file)

        database[filename] = parts

client = Client(
    intents=discord.Intents.all())

@client.event
async def on_ready():
    client.channel = await client.fetch_channel(CHANNEL_ID)
    if not client.channel:
        exit(1)

bot_thread = threading.Thread(target=lambda : client.run(TOKEN))
bot_thread.daemon = True
bot_thread.start()

# GUI code

root = tkinter.Tk()
root.title("Storecord")
root.geometry("310x200")
root.resizable(False, False)

db_list = tkinter.Listbox(root, width=35, height=11, selectmode="multiple")
db_list.grid(
    row = 0,
    column = 0,
    padx = 5,
    pady = 10,
    rowspan = 3
)

# Fill the database list
for filename, _ in database.items():
    db_list.insert(tkinter.END, filename)

def add_files():
    paths = filedialog.askopenfilenames()
    if not paths:
        return

    for path in paths:

        with open(path, "rb") as f:
            data = f.read()
        if not data:
            continue

        parts = []
        for i in range(math.ceil(len(data) / MAX_FILESIZE)):
            start, end = MAX_FILESIZE * i, MAX_FILESIZE * (i + 1)
            if end > len(data):
                parts.append(data[start:])
            else:
                parts.append(data[start : end])

        filename = os.path.basename(path)

        if not messagebox.askyesno("Uploading", f"Starting upload for '{filename}', continue?"):
            continue
        asyncio.run_coroutine_threadsafe(client.upload(filename, parts), client.loop)

        time.sleep(1) # Give the coroutines a second... not the cleanest
        while True:
            uploading = False
            for fn in os.listdir("."):
                if fn.startswith("tmp"):
                    uploading = True
                    break
            if not uploading:
                break

        db_list.insert(tkinter.END, filename)

add_button = tkinter.Button(root, text="Add Files", command=add_files, width=10)
add_button.grid(
    row = 0,
    column = 1,
    padx = 0,
    pady = 0
)

def remove_files():
    
    # Gets selected item indices
    selected = [db_list.get(i) for i in db_list.curselection()]
    
    if not selected:
        messagebox.showerror("Selection", "No items selected!")
        return
    
    for filename in selected:
        while filename in db_list.get(0, tkinter.END):
            db_list.delete(
                db_list.get(0, tkinter.END).index(filename)
            )
        database.pop(filename)

remove_button = tkinter.Button(root, text="Remove Files", command=remove_files, width=10)
remove_button.grid(
    row = 1,
    column = 1,
    padx = 0,
    pady = 0
)

def open_files():

    # Gets selected item indices
    selected = [db_list.get(i) for i in db_list.curselection()]
    
    if not selected:
        messagebox.showerror("Selection", "No items selected!")
        return
    
    for filename in selected:

        # If the file is not split, just give url
        urls = database[filename]
        if len(urls) == 1:
            webbrowser.open(urls[0])
            continue

        # It's split, download?
        filename = os.path.basename(urls[0]).split("?")[0] # ? is occasionally on the URL!
        save_as = filedialog.asksaveasfilename(initialfile=filename)
        if not save_as: # If they pressed cancel, skip
            continue

        # Combine parts and save as original filename
        parts = []
        for url in urls:
            parts.append(requests.get(url).content)
        with open(filename, "wb") as f:
            f.write(b''.join(parts))
        messagebox.showinfo("Success", f"'{filename}' saved to '{save_as}'.")


open_button = tkinter.Button(root, text="Open Files", command=open_files, width=10)
open_button.grid(
    row = 2,
    column = 1,
    padx = 0,
    pady = 0
)

root.mainloop()

# Finalise

client.loop.stop()


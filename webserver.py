from flask import Flask
from threading import Thread
import os 

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running now TERRY!"

def run():
    app.run(host="0.0.0.0", port=8000)
def keep_alive():
    t = Thread(target=run)
    t.start()



    
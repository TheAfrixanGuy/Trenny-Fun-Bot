from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Creates and starts a web server to keep the bot running on Replit"""
    t = Thread(target=run)
    t.start()

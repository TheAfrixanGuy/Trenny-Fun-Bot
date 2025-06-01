# Running Trenny Fun on Replit

This guide will help you set up and run your Discord bot on Replit.

## Setup Steps

1. **Create a Replit Account**
   - Go to [Replit](https://replit.com/) and create an account if you don't have one.

2. **Create a New Repl**
   - Click "Create Repl"
   - Select "Import from GitHub" or upload your files manually
   - If importing from GitHub, enter your repository URL
   - Choose "Python" as the language

3. **Configure Discord Token**
   - In Replit, click on the lock icon (Secrets) in the left sidebar
   - Add a new secret with the key `DISCORD_TOKEN` and your Discord bot token as the value

4. **Install Dependencies**
   - Replit will automatically install the dependencies listed in `requirements.txt`
   - If there are issues, you can manually run `pip install -r requirements.txt` in the Replit shell

5. **Run the Bot**
   - Click the "Run" button at the top of the Replit interface
   - You should see the web server start up and your bot connect to Discord

## Important Notes

- The bot uses a Flask web server to prevent Replit from shutting down due to inactivity
- If your bot gets rate limited, it will automatically restart
- Make sure your MongoDB connection string is also added to Replit Secrets if you're using MongoDB
- The bot will automatically reload the code when you make changes in Replit

## Troubleshooting

- If your bot doesn't start, check the Replit console for error messages
- Make sure all your secrets are properly set in the Secrets tab
- If you're using MongoDB, make sure your IP is whitelisted in MongoDB Atlas settings
- For rate limiting issues, consider upgrading to Replit Pro or adding more efficient code

## Keeping Your Bot Online 24/7

For 24/7 uptime:
1. Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your bot's web server URL every 5 minutes
2. Add your Replit URL (shown in the webview) to UptimeRobot as an HTTP monitor
3. This will prevent Replit from putting your bot to sleep due to inactivity

## Need Help?

If you need assistance with your bot on Replit, check the Replit documentation or join the Discord.py support server.

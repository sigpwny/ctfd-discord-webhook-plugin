# ctfd-discord-webhook-plugin

## Setup
1. Clone this repo into a folder in the plugin folder of your CTFd
2. Create a new Webhook in your discord server
3. Set the appropriate `DISCORD_WEBHOOK_URL`, `DISCORD_WEBHOOK_LIMIT`, `DISCORD_WEBHOOK_MESSAGE` environment variables or edit the `config.py` file.

If you are using docker-compose to deploy ctfd, I recommend setting the env variables within your docker-compose.yml file. Run `docker-compose build` and `docker-compose up` to rebuild and relaunch ctfd w/ the plugin included.

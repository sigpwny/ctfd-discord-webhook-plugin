from flask import request
from werkzeug.wrappers.json import JSONMixin
from CTFd.utils.dates import ctftime
from CTFd.models import Challenges, Solves
from CTFd.utils import config as ctfd_config
from CTFd.utils.user import get_current_team, get_current_user
from discord_webhook import DiscordWebhook, DiscordEmbed
from functools import wraps
from .config import config

import re

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
sanreg = re.compile(r'(~|!|@|#|\$|%|\^|&|\*|\(|\)|\_|\+|\`|-|=|\[|\]|;|\'|,|\.|\/|\{|\}|\||:|"|<|>|\?)')
sanitize = lambda m: sanreg.sub(r'\1',m)

def load(app):
    config(app)
    TEAMS_MODE = ctfd_config.is_teams_mode()

    if not app.config['DISCORD_WEBHOOK_URL']:
        print("No DISCORD_WEBHOOK_URL set! Plugin disabled.")
        return
    print("Loading plugin discord webhook!!")

    def challenge_attempt_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)

            if not ctftime():
                return result

            if isinstance(result, JSONMixin):
                data = result.json
                if isinstance(data, dict) and data.get("success") == True and isinstance(data.get("data"), dict) and data.get("data").get("status") == "correct":
                    if request.content_type != "application/json":
                        request_data = request.form
                    else:
                        request_data = request.get_json()
                    challenge_id = request_data.get("challenge_id")
                    challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()
                    solvers = Solves.query.filter_by(challenge_id=challenge.id)
                    if TEAMS_MODE:
                        solvers = solvers.filter(Solves.team.has(hidden=False))
                    else:
                        solvers = solvers.filter(Solves.user.has(hidden=False))
                    num_solves = solvers.count()

                    limit = app.config["DISCORD_WEBHOOK_LIMIT"]
                    if limit and num_solves > int(limit):
                        return result 
                    webhook = DiscordWebhook(url=app.config['DISCORD_WEBHOOK_URL'])

                    user = get_current_user()
                    team = get_current_team()

                    format_args = {
                        "team": sanitize("" if team is None else team.name),
                        "user": sanitize(user.name),
                        "challenge": sanitize(challenge.name),
                        "solves": num_solves,
                        "fsolves": ordinal(num_solves),
                        "category": sanitize(challenge.category)
                    }

                    message = app.config['DISCORD_WEBHOOK_MESSAGE'].format(**format_args)
                    embed = DiscordEmbed(description=message)
                    webhook.add_embed(embed)
                    webhook.execute()
            return result
        return wrapper

    def challenge_list_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)

            if not ctftime():
                return result

            if request.method != "POST":
                print(f"REQUEST WAS {request.method}")
                return result 

            if isinstance(result, JSONMixin):
                data = result.json
                print(f"WEBHOOK Handling data: {data}")
                if isinstance(data, dict) and data.get("success") == True and isinstance(data.get("data"), dict) and data.get("data").get("state") == "hidden":            
                    webhook = DiscordWebhook(url=app.config['DISCORD_WEBHOOK_URL'])

                    # For this route, the challenge data is returned on success. We can therefore grab it directly:

                    challenge = data.get("data")

                    format_args = {
                        "challenge": sanitize(challenge.name),
                        "category": sanitize(challenge.category)
                    }

                    message = app.config['DISCORD_WEBHOOK_CHALL_MESSAGE'].format(**format_args)
                    embed = DiscordEmbed(description=message)
                    webhook.add_embed(embed)
                    webhook.execute()
            return result
        return wrapper

    app.view_functions['api.challenges_challenge_attempt'] = challenge_attempt_decorator(app.view_functions['api.challenges_challenge_attempt'])
    app.view_functions['api.challenges_challenge_list'] = challenge_list_decorator(app.view_functions['api.challenges_challenge_list'])
 

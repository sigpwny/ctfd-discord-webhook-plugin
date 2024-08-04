from flask import request
from flask.wrappers import Response
from CTFd.utils.dates import ctftime
from CTFd.models import Challenges, Solves
from CTFd.utils import config as ctfd_config
from CTFd.utils.user import get_current_team, get_current_user
from discord_webhook import DiscordWebhook, DiscordEmbed
from functools import wraps
from .config import config

import re
from urllib.parse import quote
from types import SimpleNamespace

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
sanreg = re.compile(r'(~|!|@|#|\$|%|\^|&|\*|\(|\)|\_|\+|\`|-|=|\[|\]|;|\'|,|\.|\/|\{|\}|\||:|"|<|>|\?)')
sanitize = lambda m: sanreg.sub(r'\1',m)

def load(app):
    config(app)
    TEAMS_MODE = ctfd_config.is_teams_mode()

    if not app.config['DISCORD_WEBHOOK_URL']:
        print("No DISCORD_WEBHOOK_URL set! Plugin disabled.")
        return
    def challenge_attempt_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if not ctftime():
                return result
            if isinstance(result, Response):
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
                    if int(limit) > 0 and num_solves > int(limit):
                        return result
                    webhook = DiscordWebhook(url=app.config['DISCORD_WEBHOOK_URL'])

                    user = get_current_user()
                    team = get_current_team()

                    format_args = {
                        "team": sanitize("" if team is None else team.name),
                        "user_id": user.id,
                        "team_id": 0 if team is None else team.id,
                        "user": sanitize(user.name),
                        "challenge": sanitize(challenge.name),
                        "challenge_slug": quote(challenge.name),
                        "value": challenge.value,
                        "solves": num_solves,
                        "fsolves": ordinal(num_solves),
                        "category": sanitize(challenge.category)
                    }

                    # Add first blood support with a second message
                    if app.config["DISCORD_WEBHOOK_FSTRING"]:
                        data = SimpleNamespace(**format_args)
                        message = eval("f'{}'".format(app.config['DISCORD_WEBHOOK_MESSAGE'].replace("'", '"')))
                    else:
                        message = app.config['DISCORD_WEBHOOK_MESSAGE'].format(**format_args)
                    embed = DiscordEmbed(description=message)
                    webhook.add_embed(embed)
                    webhook.execute()
            return result
        return wrapper

    def patch_challenge_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not ctftime():
                return f(*args, **kwargs)

            # Make sure request type is "PATCH" https://docs.ctfd.io/docs/api/redoc#tag/challenges/operation/patch_challenge
            if request.method != "PATCH":
                return f(*args, **kwargs)

            # Check if feature is disabled
            if not app.config['DISCORD_WEBHOOK_CHALL']:
                return f(*args, **kwargs)

            # Check if challenge was visible beforehand (check if published/updated)
            challenge_id = kwargs.get("challenge_id")
            challenge_old = Challenges.query.filter_by(id=challenge_id).first_or_404()
            challenge_old_state = challenge_old.state

            # Run original route function
            result = f(*args, **kwargs)

            if isinstance(result, Response):
                data = result.json
                if isinstance(data, dict) and data.get("success") == True and isinstance(data.get("data"), dict):
                    # For this route, the updated challenge data is returned on success, so we grab it directly:
                    challenge = data.get("data")
                    # Check whether challenge was published,hidden or updated
                    if challenge_old_state != challenge.get("state"):
                        if challenge.get("state") == "hidden":
                            action = "hidden"
                        else:
                            action = "published"
                    else:
                        action = "updated"

                    # Make sure the challenge is visible, action is hidden, or override is configured
                    if not (data.get("data").get("state") == "visible" or action == "hidden" or app.config['DISCORD_WEBHOOK_CHALL_UNPUBLISHED']):
                        return result

                    if action == "updated" and not app.config['DISCORD_WEBHOOK_CHALL_UPDATE']:
                        return result

                    format_args = {
                        "challenge": sanitize(challenge.get("name")),
                        "category": sanitize(challenge.get("category")),
                        "action": sanitize(action)
                    }

                    webhook = DiscordWebhook(url=app.config['DISCORD_WEBHOOK_URL'])
                    message = app.config['DISCORD_WEBHOOK_CHALL_MESSAGE'].format(**format_args)
                    embed = DiscordEmbed(description=message)
                    webhook.add_embed(embed)
                    webhook.execute()
            return result
        return wrapper

    app.view_functions['api.challenges_challenge_attempt'] = challenge_attempt_decorator(app.view_functions['api.challenges_challenge_attempt'])
    app.view_functions['api.challenges_challenge'] = patch_challenge_decorator(app.view_functions['api.challenges_challenge'])
 

from os import environ

def config(app):
    '''
    Discord webhook URL to send data to. Set to None to disable plugin entirely.
    '''
    app.config['DISCORD_WEBHOOK_URL'] = environ.get('DISCORD_WEBHOOK_URL')

    '''
    Limit on number of solves for challenge to trigger webhook for. Set to 0 to send a message for every solve.
    '''
    app.config['DISCORD_WEBHOOK_LIMIT'] = environ.get('DISCORD_WEBHOOK_LIMIT', '3')

    '''
    Webhook flag submission format string. Valid vars: team, user, solves, fsolves (formatted solves), challenge, category, team_id, user_id, challenge_slug, value
    '''
    app.config['DISCORD_WEBHOOK_MESSAGE'] = environ.get('DISCORD_WEBHOOK_MESSAGE', 'Congratulations to team {team} for the {fsolves} solve on challenge {challenge}!')

    '''
    Post webhook message when challenge is changed (published, hidden or updated)
    '''
    app.config['DISCORD_WEBHOOK_CHALL'] = environ.get('DISCORD_WEBHOOK_CHALL', True)

    '''
    Post webhook message when challenge is updated (otherwise only published or hidden)
    '''
    app.config['DISCORD_WEBHOOK_CHALL_UPDATE'] = environ.get('DISCORD_WEBHOOK_CHALL_UPDATE', False)

    '''
    Post webhook message even if challenge has not yet been published (only relevant when update is enabled)
    '''
    app.config['DISCORD_WEBHOOK_CHALL_UNPUBLISHED'] = environ.get('DISCORD_WEBHOOK_CHALL_UNPUBLISHED', False)

    '''
    Webhook challenge change format string. Valid vars: challenge, category, action (published, hidden or updated)
    '''
    app.config['DISCORD_WEBHOOK_CHALL_MESSAGE'] = environ.get('DISCORD_WEBHOOK_CHALL_MESSAGE', 'Challenge {challenge} has been {action}!')

    '''
    Turning this on turns your DISCORD_WEBHOOK_CHALL_MESSAGE into a f-string. Values can be accessed with data.<field>

    This allows conditional formatting: e.g. {'FIRST BLOOD' if data.solves == 1 else ''}
    '''
    app.config['DISCORD_WEBHOOK_FSTRING'] = environ.get('DISCORD_WEBHOOK_FSTRING', False)
from os import environ

def config(app):
    '''
    Discord webhook URL to send data to. Set to None to disable plugin entirely.
    '''
    app.config['DISCORD_WEBHOOK_URL'] = environ.get('DISCORD_WEBHOOK_URL')

    '''
    Limit on number of solves for challenge to trigger webhook for. Set to None to send a message for every solve.
    '''
    app.config['DISCORD_WEBHOOK_LIMIT'] = environ.get('DISCORD_WEBHOOK_LIMIT', '3')

    '''
    Webhook message format string. Valid vars: team, user, solves, fsolves (formatted solves), challenge, category
    '''
    app.config['DISCORD_WEBHOOK_MESSAGE'] = environ.get('DISCORD_WEBHOOK_MESSAGE', 'Congratulations to team {team} for the {fsolves} solve on challenge {challenge}!')


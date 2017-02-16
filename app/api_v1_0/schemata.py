"""Schemata used to validate incoming API data."""


class Schemata(object):
    post_profile = {
        'type': 'object',
        'properties': {
            'external_id': {'type': 'string'},
        }
    }

    put_profile = {
        'type': 'object',
        'properties': {}
    }

    post_reaction = {
        'type': 'object',
        'properties': {
            'profile': {'type': 'string'},
            'statement': {'type': 'string'},
            'reaction': {'type': 'integer'}
        }
    }

    post_cron = {
        'type': 'object',
        'properties': {
            'action': {'type': 'string'}
        }
    }

schemata = Schemata()

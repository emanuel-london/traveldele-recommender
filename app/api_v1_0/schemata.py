"""Schemata used to validate incoming API data."""


class Schemata(object):

    get_matches = {
        'type': 'object',
        'properties': {
            'sort_similarity': {'type': 'integer', 'required': False},
            'limit': {'type': 'integer', 'required': False}
        }
    }

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

    put_reaction = {
        'type': 'object',
        'properties': {}
    }

    get_inaction = {
        'type': 'object',
        'properties': {
            'tags': {
                'type': 'array',
                'minItems': 1,
                'items': {'type': 'string'}
            }
        }
    }

    post_cron = {
        'type': 'object',
        'properties': {
            'action': {'type': 'string'}
        }
    }

schemata = Schemata()

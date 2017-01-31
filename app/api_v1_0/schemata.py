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

    post_answer = {
        'type': 'object',
        'properties': {
            'profile': {'type': 'string'},
            'question': {'type': 'string'},
            'answer': {'type': 'string'}
        }
    }

schemata = Schemata()

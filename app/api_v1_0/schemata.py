"""Schemata used to validate incoming API data."""


class Schemata(object):
    post_profile = {
        'type': 'object',
        'properties': {
            'external_id': {'type': 'string'},
            'name': {'type': 'string'}
        }
    }

    put_profile = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'required': False}
        }
    }

schemata = Schemata()

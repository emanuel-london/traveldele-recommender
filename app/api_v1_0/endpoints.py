"""Implements endpoints for the Kooyara API version 1.0."""


from http import HTTPStatus
import random

from bson.objectid import ObjectId
from bson.errors import InvalidId
from flask import (
    current_app, jsonify, request,
)
import validictory

from app import (
    app, mongo, oauth_provider as op,
)
from app.api_v1_0 import api_v1_0
from app.api_v1_0.schemata import schemata
from app.utils.decorators import async


@api_v1_0.route('/', methods=['GET'])
def index():
    """Dummy endpoint. 
    Makes it easy to get base url in other parts of the app.
    """
    return jsonify({
        'status': HTTPStatus.OK,
        'message': 'API version 1.0'
    }), HTTPStatus.OK


@api_v1_0.route('/matches/<string:_id>', methods=['GET', 'POST'])
@op.require_oauth('api')
def get_matches(_id):
    profile = mongo.db.profiles

    try:
        check = profile.find_one({'_id': ObjectId(_id)})
        # If the profile was found, return it's matches.
        if check is not None:
            output = []

            if request.method == 'GET':
                matches = current_app.rs.get_matches(ObjectId(_id))
                for match in matches:
                    mp = profile.find_one({'_id': match[0]})
                    output.append({
                        '_id': str(mp['_id']),
                        'external_id': mp['external_id'],
                        'similarity': round(match[1], 3)
                    })
            else:
                # Get request data.
                data = request.get_json()
                if data is None:
                    return jsonify({
                        'status': HTTPStatus.BAD_REQUEST,
                        'message': '{0}. Only JSON data allowed.'.format(HTTPStatus.BAD_REQUEST.description)
                    }), HTTPStatus.BAD_REQUEST

                # Validate data against the appropriate schema.
                try:
                    validictory.validate(data, schemata.get_matches)
                except Exception:
                    # Invalid data.
                    return jsonify({
                        'status': HTTPStatus.BAD_REQUEST,
                        'message': '{0}. Invalid data schema.'.format(HTTPStatus.BAD_REQUEST.description)
                    }), HTTPStatus.BAD_REQUEST

                if 'sort_similarity' in data:
                    matches = current_app.rs.get_matches(
                        ObjectId(_id), sort_sim=data['sort_similarity'])
                else:
                    matches = current_app.rs.get_matches(ObjectId(_id))

                for match in matches:
                    mp = profile.find_one({"_id": match[0]})
                    output.append({
                        '_id': str(mp['_id']),
                        'external_id': mp['external_id'],
                        'similarity': round(match[1], 3)
                    })
                    if 'limit' in data:
                        if len(output) >= data['limit']:
                            break

            return jsonify({
                'status': HTTPStatus.OK,
                'result': output
            }), HTTPStatus.OK

        # Profile was not found. Return error message with 404.
        return jsonify({
            'status': HTTPStatus.NOT_FOUND,
            'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
        }), HTTPStatus.NOT_FOUND

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/statement', methods=['GET'])
@op.require_oauth('api')
def statements():
    """Retrieve all statements from the recommender system."""
    statement = mongo.db.statements
    output = []
    for s in statement.find():
        output.append({'_id': str(s['_id']), 'statement': s['statement']})

    return jsonify({
        'status': HTTPStatus.OK,
        'result': output
    }), HTTPStatus.OK


@api_v1_0.route('/statement/inaction/<string:_id>', methods=['GET', 'POST'])
@op.require_oauth('api')
def get_inaction_statement(_id):
    """Randomly select a statement with no reaction and return it."""
    try:
        reaction = mongo.db.reactions
        reacted = [a['statement']
                   for a in reaction.find({'profile': ObjectId(_id)})]

        statement = mongo.db.statements
        inaction = []
        if request.method == 'GET':
            inaction = statement.find({'_id': {'$nin': reacted}})
        else:
            # Get request data.
            data = request.get_json()
            if data is None:
                return jsonify({
                    'status': HTTPStatus.BAD_REQUEST,
                    'message': '{0}. Only JSON data allowed.'.format(HTTPStatus.BAD_REQUEST.description)
                }), HTTPStatus.BAD_REQUEST

            # Validate data against the appropriate schema.
            try:
                validictory.validate(data, schemata.get_inaction)
            except Exception:
                # Invalid data.
                return jsonify({
                    'status': HTTPStatus.BAD_REQUEST,
                    'message': '{0}. Invalid data schema.'.format(HTTPStatus.BAD_REQUEST.description)
                }), HTTPStatus.BAD_REQUEST
            inaction = statement.find(
                {'$and': [{'_id': {'$nin': reacted}}, {'tags': {'$all': data['tags']}}]})

        # Select one statement at random.
        if inaction.count() > 0:
            ret = random.choice(list(inaction))

            output = {
                '_id': str(ret['_id']),
                'statement': ret['statement']
            }
        else:
            output = {}

        return jsonify({
            'status': HTTPStatus.OK,
            'result': output
        }), HTTPStatus.OK

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/reaction', methods=['POST'])
@op.require_oauth('api')
def post_reaction():
    """Save a reaction associated with a specific profile and statement."""
    reaction = mongo.db.reactions

    # Get request data.
    data = request.get_json()
    if data is None:
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Only JSON data allowed.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Validate data against the appropriate schema.
    try:
        validictory.validate(data, schemata.post_reaction)
    except Exception:
        # Invalid data.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid data schema.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Insert reaction.
    result = reaction.insert_one({
        'profile': ObjectId(data['profile']),
        'statement': ObjectId(data['statement']),
        'reaction': data['reaction']
    })
    output = {
        'inserted_id': str(result.inserted_id)
    }

    # Notify recommender system.
    @async
    def update_sims():
        with app.app_context():
            up = current_app.rs.add_reaction(result.inserted_id)
            current_app.rs.update_similarity(filter_by=up)

    update_sims()

    return jsonify({
        'status': HTTPStatus.OK,
        'result': output
    }), HTTPStatus.OK


@api_v1_0.route('/reaction/<string:_id>', methods=['PUT'])
@op.require_oauth('api')
def put_reaction(_id):
    """Update an existing reaction in the recommender system."""
    reaction = mongo.db.reactions

    # Get request data.
    data = request.get_json()
    if data is None:
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Only JSON data allowed.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Validate data against the appropriate schema.
    try:
        validictory.validate(data, schemata.put_reaction)
    except Exception:
        # Invalid data.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid data schema.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    try:
        document = reaction.find_one({'_id': ObjectId(_id)})
        if document is None:
            return jsonify({
                'status': HTTPStatus.NOT_FOUND,
                'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
            }), HTTPStatus.NOT_FOUND

        changes = {}
        for key, value in data.items():
            changes[key] = value

        # Perform update.
        stat = reaction.update_one(
            {'_id': ObjectId(_id)},
            {'$set': changes}
        )

        # Update successful.
        if stat.acknowledged:
            return jsonify({
                'status': HTTPStatus.OK,
                'result': {'updated_id': _id}
            }), HTTPStatus.OK

        # Update not successful.
        return jsonify({
            'status': HTTPStatus.INTERNAL_SERVER_ERROR,
            'message': '{0}. Resource not updated.'.format(HTTPStatus.INTERNAL_SERVER_ERROR.description)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/reaction/profile/<string:_id>', methods=['GET'])
@op.require_oauth('api')
def get_reactions(_id):
    profile = mongo.db.profiles

    try:
        check = profile.find_one({'_id': ObjectId(_id)})
        # If the profile was found, return it's matches.
        if check is not None:
            output = []
            reactions = mongo.db.reactions.find({'profile': ObjectId(_id)})

            for reaction in reactions:
                output.append({
                    'statement': str(reaction['statement']),
                    'reaction': reaction['reaction']
                })

            return jsonify({
                'status': HTTPStatus.OK,
                'result': output
            }), HTTPStatus.OK

        # Profile was not found. Return error message with 404.
        return jsonify({
            'status': HTTPStatus.NOT_FOUND,
            'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
        }), HTTPStatus.NOT_FOUND

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/reaction/<string:_id>', methods=['GET'])
@op.require_oauth('api')
def get_reaction(_id):
    """Retrieve a reaction from the recommender system by its _id."""
    reaction = mongo.db.reactions

    try:
        out = reaction.find_one({'_id': ObjectId(_id)})
        # If the profile was found, return it.
        if out is not None:
            output = {
                '_id': str(out['_id']),
                'profile': str(out['profile']),
                'statement': str(out['statement']),
                'reaction': out['reaction']
            }

            return jsonify({
                'status': HTTPStatus.OK,
                'result': output
            }), HTTPStatus.OK

        # Profile was not found. Return error message with 404.
        return jsonify({
            'status': HTTPStatus.NOT_FOUND,
            'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
        }), HTTPStatus.NOT_FOUND

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/reaction/<string:_id>', methods=['DELETE'])
@op.require_oauth('api')
def delete_reaction(_id):
    """Delete a reaction from the recommender system."""
    reaction = mongo.db.reactions

    try:
        document = reaction.find_one({'_id': ObjectId(_id)})
        if document is None:
            return jsonify({
                'status': HTTPStatus.NOT_FOUND,
                'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
            }), HTTPStatus.NOT_FOUND

        stat = reaction.delete_one({'_id': ObjectId(_id)})

        # Delete was successful.
        if stat.deleted_count == 1:
            return jsonify({
                'status': HTTPStatus.OK,
                'result': {'deleted_id': _id}
            }), HTTPStatus.OK

        # Delete was not successful.
        return jsonify({
            'status': HTTPStatus.INTERNAL_SERVER_ERROR,
            'message': '{0}. Resource not deleted.'.format(HTTPStatus.INTERNAL_SERVER_ERROR.description)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/profile', methods=['GET'])
@op.require_oauth('api')
def get_profiles():
    """Retrieve all profiles from the recommender system."""
    profile = mongo.db.profiles
    output = []
    for p in profile.find():
        out = {
            '_id': str(p['_id']),
            'external_id': p['external_id']
        }
        output.append(out)

    return jsonify({
        'status': HTTPStatus.OK,
        'result': output
    }), HTTPStatus.OK


@api_v1_0.route('/profile/<string:_id>', methods=['GET'])
@op.require_oauth('api')
def get_profile(_id):
    """Retrieve a profile from the recommender system by its _id."""
    profile = mongo.db.profiles

    try:
        out = profile.find_one({'_id': ObjectId(_id)})
        # If the profile was found, return it.
        if out is not None:
            output = {
                '_id': str(out['_id']),
                'external_id': out['external_id']
            }

            return jsonify({
                'status': HTTPStatus.OK,
                'result': output
            }), HTTPStatus.OK

        # Profile was not found. Return error message with 404.
        return jsonify({
            'status': HTTPStatus.NOT_FOUND,
            'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
        }), HTTPStatus.NOT_FOUND

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/profile', methods=['POST'])
@op.require_oauth('api')
def post_profile():
    """Create a new profile in the recommender system."""
    profile = mongo.db.profiles

    # Get request data.
    data = request.get_json()
    if data is None:
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Only JSON data allowed.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Validate data against the appropriate schema.
    try:
        validictory.validate(data, schemata.post_profile)
    except Exception:
        # Invalid data.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid data schema.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Check that the external_id is unique.
    eid_check = profile.find_one({'external_id': data['external_id']})
    if eid_check is not None:
        # Duplicate.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Insert profile.
    result = profile.insert_one({
        'external_id': data['external_id']
    })
    output = {
        'inserted_id': str(result.inserted_id)
    }
    return jsonify({
        'status': HTTPStatus.OK,
        'result': output
    }), HTTPStatus.OK


@api_v1_0.route('/profile/<string:_id>', methods=['PUT'])
@op.require_oauth('api')
def put_profile(_id):
    """Update an existing profile in the recommender system."""
    profile = mongo.db.profiles

    # Get request data.
    data = request.get_json()
    if data is None:
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Only JSON data allowed.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Validate data against the appropriate schema.
    try:
        validictory.validate(data, schemata.put_profile)
    except Exception:
        # Invalid data.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid data schema.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    try:
        document = profile.find_one({'_id': ObjectId(_id)})
        if document is None:
            return jsonify({
                'status': HTTPStatus.NOT_FOUND,
                'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
            }), HTTPStatus.NOT_FOUND

        changes = {}
        for key, value in data.items():
            if key in ['name']:  # Only update known fields.
                changes[key] = value

        # Perform update.
        stat = profile.update_one(
            {'_id': ObjectId(_id)},
            {'$set': changes}
        )

        # Update successful.
        if stat.acknowledged:
            return jsonify({
                'status': HTTPStatus.OK,
                'result': {'updated_id': _id}
            }), HTTPStatus.OK

        # Update not successful.
        return jsonify({
            'status': HTTPStatus.INTERNAL_SERVER_ERROR,
            'message': '{0}. Resource not updated.'.format(HTTPStatus.INTERNAL_SERVER_ERROR.description)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/profile/<string:_id>', methods=['DELETE'])
@op.require_oauth('api')
def delete_profile(_id):
    """Delete a profile from the recommender system."""
    profile = mongo.db.profiles

    try:
        document = profile.find_one({'_id': ObjectId(_id)})
        if document is None:
            return jsonify({
                'status': HTTPStatus.NOT_FOUND,
                'message': '{0}.'.format(HTTPStatus.NOT_FOUND.description)
            }), HTTPStatus.NOT_FOUND

        stat = profile.delete_one({'_id': ObjectId(_id)})

        # Delete was successful.
        if stat.deleted_count == 1:

            # Notify recommender system.
            @async
            def update_sims():
                with app.app_context():
                    current_app.rs.clear_orphans(ObjectId(_id))
                    current_app.rs.update_similarity()

            update_sims()

            return jsonify({
                'status': HTTPStatus.OK,
                'result': {'deleted_id': _id}
            }), HTTPStatus.OK

        # Delete was not successful.
        return jsonify({
            'status': HTTPStatus.INTERNAL_SERVER_ERROR,
            'message': '{0}. Resource not deleted.'.format(HTTPStatus.INTERNAL_SERVER_ERROR.description)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

    except InvalidId:
        # Invalid _id format.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid _id format.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST


@api_v1_0.route('/cron', methods=['POST'])
@op.require_oauth('admin')
def post_cron():
    """Submit a cron job to the api."""

    # Get request data.
    data = request.get_json()
    if data is None:
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Only JSON data allowed.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    # Validate data against the appropriate schema.
    try:
        validictory.validate(data, schemata.post_cron)
    except Exception:
        # Invalid data.
        return jsonify({
            'status': HTTPStatus.BAD_REQUEST,
            'message': '{0}. Invalid data schema.'.format(HTTPStatus.BAD_REQUEST.description)
        }), HTTPStatus.BAD_REQUEST

    getattr(current_app.rs, data['action'])()

    return jsonify({
        'status': HTTPStatus.OK,
        'message': 'Job submitted.'
    }), HTTPStatus.OK

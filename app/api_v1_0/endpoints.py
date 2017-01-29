"""Implements endpoints for the Kooyara API version 1.0."""


from http import HTTPStatus


from bson.objectid import ObjectId
from bson.errors import InvalidId
from flask import (
    jsonify, request,
)
import validictory

from app import (
    mongo, oauth_provider as op,
)
from app.api_v1_0 import api_v1_0
from app.api_v1_0.schemata import schemata


@api_v1_0.route('/question', methods=['GET'])
@op.require_oauth('api')
def questions():
    """Retrieve all questions from the recommender system."""
    question = mongo.db.questions
    output = []
    for q in question.find():
        output.append({'_id': str(q['_id']), 'question': q['question']})

    return jsonify({
        'status': HTTPStatus.OK,
        'result': output
    }), HTTPStatus.OK


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

            for key in ['name']:
                if key in out.keys():
                    output[key] = out[key]

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

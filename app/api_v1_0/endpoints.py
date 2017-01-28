"""Implements endpoints for the Kooyara API version 1.0."""


from flask import jsonify


from app import (
    mongo, oauth_provider as op,
)
from app.api_v1_0 import api_v1_0


@api_v1_0.route('/question', methods=['GET'])
@op.require_oauth('api')
def get_all_questions():
    """"""
    question = mongo.db.questions
    output = []
    for q in question.find():
        output.append({'_id': str(q['_id']), 'question': q['question']})
    return jsonify({'status': 'OK', 'result': output})
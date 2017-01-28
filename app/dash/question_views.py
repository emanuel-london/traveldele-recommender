"""Implements dashboard endpoints."""


import json


from bson.objectid import ObjectId
from flask import (
    current_app, flash, redirect,
    render_template, url_for,
)
from flask_breadcrumbs import register_breadcrumb


from app import mongo
from app.confirm import confirm_required
from app.dash import dash
from app.dash.question_forms import (
    EditQuestionForm, NewQuestionForm,
)
from app.utils.decorators import admin_required


@dash.route('/questions')
@admin_required
@register_breadcrumb(dash, 'bc.dash.questions', 'Recommender System Questions')
def questions():
    """List recommender system questions"""
    question = mongo.db.questions
    questions = []
    for q in question.find():
        questions.append({'_id': str(q['_id']), 'question': q['question']})

    page_vars = {
        'title': 'Recommender System Questions',
        'navwell': True,
        'page_header': 'Recommender System Questions',
        'questions': questions
    }
    return render_template('dash/questions/questions.html', **page_vars)


@dash.route('/questions/new', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.questions.new', 'New Question')
def new_question():
    """Render a form allowing the user to add a new question to the
    document database.
    """

    form = NewQuestionForm()

    if form.validate_on_submit():
        question = mongo.db.questions
        qid = question.insert({
            'question': form.question.data,
            'options': form.options.data
        })

        flash('Question ({0}) added to document store.'.format(qid), 'success')
        return redirect(url_for('dash.question', qid=qid))

    form.options.data = """Yes\nNo"""

    page_vars = {
        'title': 'New Question',
        'navwell': True,
        'page_header': 'New Question',
        'form': form
    }
    return render_template('dash/questions/new-question.html', **page_vars)


@dash.route('/questions/<string:qid>/edit', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.questions.edit', 'Edit Question')
def question(qid):
    """Render a form to edit an existing question."""
    question = mongo.db.questions
    q = question.find_one({'_id': ObjectId(qid)})

    form = EditQuestionForm()

    if form.validate_on_submit():
        stat = question.update(
            {'_id': ObjectId(qid)},
            {
                'question': form.question.data,
                'options': form.options.data
            }
        )

        if stat['updatedExisting']:
            flash('Changes saved.', 'success')
        else:
            flash('Could not save changes.', 'danger')
        return redirect(url_for('dash.question', qid=qid))

    form.question.data = q['question']
    form.options.data = q['options']

    page_vars = {
        'title': 'Edit Question',
        'navwell': True,
        'page_header': 'Edit Question',
        'form': form,
        'qid': qid
    }
    return render_template('dash/questions/edit-question.html', **page_vars)


@dash.route('/questions/<string:qid>/delete')
@admin_required
@confirm_required(
    'Are you sure you want to delete this question?',
    'I am sure', 'dash.question', ['qid'], 'danger'
)
def delete_question(qid):
    """Remove a question from the document database."""
    question = mongo.db.questions
    question.remove({'_id': ObjectId(qid)}, True)
    flash('Question successfully deleted.', 'success')
    return redirect(url_for('dash.questions'))


@dash.route('/questions/purge')
@admin_required
@confirm_required(
    'Are you sure you want to purge all questions from the document database?',
    'I am sure', 'dash.questions', severity='danger'
)
def purge_questions():
    """Purge all questions from the document database."""
    question = mongo.db.questions
    question.remove({})
    flash('Questions successfully purged.', 'success')
    return redirect(url_for('dash.questions'))


@dash.route('questions/import')
@admin_required
def import_questions():
    """Import questions from json file in data folder."""
    question = mongo.db.questions
    data_file = '{0}/questions.json'.format(current_app.config['DATA_FILES'])
    with open(data_file, 'r') as fp:
        data = json.load(fp)
        for q in data['questions']:
            question.insert({
                'question': q['question'],
                'options': '\n'.join(q['options'])
            })

    flash('Questions successfully imported.', 'success')
    return redirect(url_for('dash.questions'))

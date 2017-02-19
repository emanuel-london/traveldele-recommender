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
from app.dash.statement_forms import (
    EditStatementForm, NewStatementForm,
)
from app.utils.decorators import admin_required


@dash.route('/statements')
@admin_required
@register_breadcrumb(dash, 'bc.dash.statements', 'Recommender System Statements')
def statements():
    """List recommender system statements"""
    statement = mongo.db.statements
    statements = []
    for s in statement.find():
        statements.append({
            '_id': str(s['_id']),
            'statement': s['statement'],
            'category': str(s['category'])
        })

    category = mongo.db.categories
    categories = {}
    for c in category.find():
        categories[str(c['_id'])] = c['category']

    page_vars = {
        'title': 'Recommender System Statements',
        'navwell': True,
        'page_header': 'Recommender System Statements',
        'statements': statements,
        'categories': categories
    }
    return render_template('dash/statements/statements.html', **page_vars)


@dash.route('/statements/new', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.statements.new', 'New Statement')
def new_statement():
    """Render a form allowing the user to add a new statement to the
    document database.
    """
    category = mongo.db.categories

    form = NewStatementForm()

    choices = []
    for c in category.find():
        choices.append((str(c['_id']), c['category']))

    form.category.choices = choices

    if form.validate_on_submit():
        statement = mongo.db.statements
        sid = statement.insert({
            'statement': form.statement.data,
            'category': ObjectId(form.category.data),
            'tags': [x.strip() for x in form.tags.data.split(',')]
        })

        flash(
            'Statement ({0}) added to document store.'.format(sid), 'success')
        return redirect(url_for('dash.statement', sid=sid))

    page_vars = {
        'title': 'New Statement',
        'navwell': True,
        'page_header': 'New Statement',
        'form': form
    }
    return render_template('dash/statements/new-statement.html', **page_vars)


@dash.route('/statements/<string:sid>/edit', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.statements.edit', 'Edit Statement')
def statement(sid):
    """Render a form to edit an existing statement."""
    category = mongo.db.categories
    statement = mongo.db.statements
    s = statement.find_one({'_id': ObjectId(sid)})

    form = EditStatementForm()

    choices = []
    for c in category.find():
        choices.append((str(c['_id']), c['category']))

    form.category.choices = choices

    if form.validate_on_submit():
        stat = statement.update(
            {'_id': ObjectId(sid)},
            {
                '$set': {
                    'statement': form.statement.data,
                    'category': ObjectId(form.category.data),
                    'tags': [x.strip() for x in form.tags.data.split(',')]
                }
            }
        )

        if stat['updatedExisting']:
            flash('Changes saved.', 'success')
        else:
            flash('Could not save changes.', 'danger')
        return redirect(url_for('dash.statement', sid=sid))

    form.statement.data = s['statement']
    form.category.data = str(s['category'])

    if 'tags' in s:
        form.tags.data = ', '.join(s['tags'])

    page_vars = {
        'title': 'Edit Statement',
        'navwell': True,
        'page_header': 'Edit Statement',
        'form': form,
        'sid': sid
    }
    return render_template('dash/statements/edit-statement.html', **page_vars)


@dash.route('/statements/<string:sid>/delete')
@admin_required
@confirm_required(
    'Are you sure you want to delete this statement?',
    'I am sure', 'dash.statement', ['sid'], 'danger'
)
def delete_statement(sid):
    """Remove a statement from the document database."""
    # Remove all reactions associated with this statement, as they are no
    # longer valid.
    reaction = mongo.db.reactions
    reaction.remove({"statement": ObjectId(sid)})

    # Remove the statement.
    statement = mongo.db.statements
    statement.remove({'_id': ObjectId(sid)}, True)
    flash('Statement successfully deleted.', 'success')
    return redirect(url_for('dash.statements'))


@dash.route('/statements/purge')
@admin_required
@confirm_required(
    'Are you sure you want to purge all statements from the document database?',
    'I am sure', 'dash.statements', severity='danger'
)
def purge_statements():
    """Purge all statements from the document database."""
    # Remove all reactions as they are no longer valid.
    reaction = mongo.db.reactions
    reaction.remove({})

    # Remove all statements.
    statement = mongo.db.statements
    statement.remove({})

    flash('Statements successfully purged.', 'success')
    return redirect(url_for('dash.statements'))


@dash.route('statements/import')
@admin_required
def import_statements():
    """Import statements from json file in data folder."""
    category = mongo.db.categories
    statement = mongo.db.statements
    data_file = '{0}/statements.json'.format(current_app.config['DATA_FILES'])
    with open(data_file, 'r') as fp:
        data = json.load(fp)
        for s in data['statements']:
            c = category.find_one({"category": s['category']})
            statement.insert({
                'statement': s['statement'],
                'category': c['_id']
            })

    flash('Statements successfully imported.', 'success')
    return redirect(url_for('dash.statements'))

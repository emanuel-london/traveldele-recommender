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
        statements.append({'_id': str(s['_id']), 'statement': s['statement']})

    page_vars = {
        'title': 'Recommender System Statements',
        'navwell': True,
        'page_header': 'Recommender System Statements',
        'statements': statements
    }
    return render_template('dash/statements/statements.html', **page_vars)


@dash.route('/statements/new', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.statements.new', 'New Statement')
def new_statement():
    """Render a form allowing the user to add a new statement to the
    document database.
    """

    form = NewStatementForm()

    if form.validate_on_submit():
        statement = mongo.db.statements
        sid = statement.insert({
            'statement': form.statement.data
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
    statement = mongo.db.statements
    s = statement.find_one({'_id': ObjectId(sid)})

    form = EditStatementForm()

    if form.validate_on_submit():
        stat = statement.update(
            {'_id': ObjectId(sid)},
            {
                'statement': form.statement.data
            }
        )

        if stat['updatedExisting']:
            flash('Changes saved.', 'success')
        else:
            flash('Could not save changes.', 'danger')
        return redirect(url_for('dash.statement', sid=sid))

    form.statement.data = s['statement']

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
    statement = mongo.db.statements
    statement.remove({})
    flash('Statements successfully purged.', 'success')
    return redirect(url_for('dash.statements'))


@dash.route('statements/import')
@admin_required
def import_statements():
    """Import statements from json file in data folder."""
    statement = mongo.db.statements
    data_file = '{0}/statements.json'.format(current_app.config['DATA_FILES'])
    with open(data_file, 'r') as fp:
        data = json.load(fp)
        for s in data['statements']:
            statement.insert({
                'statement': s['statement']
            })

    flash('Statements successfully imported.', 'success')
    return redirect(url_for('dash.statements'))
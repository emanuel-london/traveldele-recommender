"""Implements dashboard endpoints for the categories section."""


import json


from bson.objectid import ObjectId
from flask import (
    current_app, flash, redirect,
    render_template, request, url_for,
)
from flask_breadcrumbs import register_breadcrumb


from app import mongo
from app.confirm import confirm_required
from app.dash import dash
from app.dash.category_forms import (
    EditCategoryForm, NewCategoryForm,
)
from app.utils.decorators import admin_required


@dash.route('/categories', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.categories', 'Recommender System Categories')
def categories():
    """List recommender system categories"""
    category = mongo.db.categories

    if request.method == 'POST':
        data = {}
        for cid in list(request.form):
            data[cid] = float(request.form.get(cid))
        total = round(sum(x for x in data.values()), 1)
        if total != 1.0:
            flash(
                'Sum of weights must equal 1.', 'danger')
        else:
            for cid, weight in data.items():
                category.update(
                    {'_id': ObjectId(cid)},
                    {
                        '$set': {'weight': weight}
                    }
                )
            flash('Weights successfully updated.', 'success')
        return redirect(url_for('dash.categories'))

    categories = []
    for c in category.find():
        categories.append({
            '_id': str(c['_id']),
            'category': c['category'],
            'weight': c['weight']
        })

    page_vars = {
        'title': 'Recommender System Categories',
        'navwell': True,
        'page_header': 'Recommender System Categories',
        'categories': categories
    }
    return render_template('dash/categories/categories.html', **page_vars)


@dash.route('/categories/new', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.categories.new', 'New Category')
def new_category():
    """Render a form allowing the user to add a new category to the
    document database.
    """

    form = NewCategoryForm()

    if form.validate_on_submit():
        category = mongo.db.categories
        cid = category.insert({
            'category': form.category.data,
            'weight': float(form.weight.data)
        })

        flash(
            'Category ({0}) added to document store.'.format(cid), 'success')
        return redirect(url_for('dash.category', cid=cid))

    form.weight.data = '0.0'

    page_vars = {
        'title': 'New Category',
        'navwell': True,
        'page_header': 'New Category',
        'form': form
    }
    return render_template('dash/categories/new-category.html', **page_vars)


@dash.route('/categories/<string:cid>/edit', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.categories.edit', 'Edit Category')
def category(cid):
    """Render a form to edit an existing category."""
    category = mongo.db.categories
    c = category.find_one({'_id': ObjectId(cid)})

    form = EditCategoryForm()

    if form.validate_on_submit():
        stat = category.update(
            {'_id': ObjectId(cid)},
            {
                'category': form.category.data,
                'weight': float(form.weight.data)
            }
        )

        if stat['updatedExisting']:
            flash('Changes saved.', 'success')
        else:
            flash('Could not save changes.', 'danger')
        return redirect(url_for('dash.category', cid=cid))

    form.category.data = c['category']
    form.weight.data = c['weight']

    page_vars = {
        'title': 'Edit Category',
        'navwell': True,
        'page_header': 'Edit Category',
        'form': form,
        'cid': cid
    }
    return render_template('dash/categories/edit-category.html', **page_vars)


@dash.route('/categories/<string:cid>/delete')
@admin_required
@confirm_required(
    'Are you sure you want to delete this category?',
    'I am sure', 'dash.category', ['cid'], 'danger'
)
def delete_category(cid):
    """Remove a category from the document database."""
    # Update all statements referencing this category.
    statement = mongo.db.statements
    statement.update_many(
        {"category": ObjectId(cid)},
        {
            "$set": {"category": None}
        }
    )

    # Remove the category.
    category = mongo.db.categories
    category.remove({'_id': ObjectId(cid)}, True)
    flash('Category successfully deleted.', 'success')
    return redirect(url_for('dash.categories'))


@dash.route('/categories/purge')
@admin_required
@confirm_required(
    'Are you sure you want to purge all categories from the document database?',
    'I am sure', 'dash.categories', severity='danger'
)
def purge_categories():
    """Purge all categories from the document database."""
    category = mongo.db.categories
    category.remove({})
    flash('Categories successfully purged.', 'success')
    return redirect(url_for('dash.categories'))


@dash.route('categories/import')
@admin_required
def import_categories():
    """Import categories from json file in data folder."""
    category = mongo.db.categories
    data_file = '{0}/categories.json'.format(current_app.config['DATA_FILES'])
    with open(data_file, 'r') as fp:
        data = json.load(fp)
        for c in data['categories']:
            category.insert({
                'category': c['category'],
                'weight': float(c['weight'])
            })

    flash('Categories successfully imported.', 'success')
    return redirect(url_for('dash.categories'))

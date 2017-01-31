"""Implements dashboard endpoints."""


from bson.objectid import ObjectId


from flask import (
    flash, redirect, render_template, url_for,
)
from flask_breadcrumbs import register_breadcrumb


from app import (
    mongo, sql,
)
from app.confirm import confirm_required
from app.dash import dash
from app.dash.profile_forms import (
    EditProfileForm, NewProfileForm,
)
from app.utils.decorators import admin_required
from app.utils.models import Profile


@dash.route('/profiles')
@admin_required
@register_breadcrumb(dash, 'bc.dash.profiles', 'Test Profiles')
def profiles():
    """List test profiles"""

    profiles = Profile.query.all()

    page_vars = {
        'title': 'Test Profiles',
        'navwell': True,
        'page_header': 'Test Profiles',
        'profiles': profiles
    }
    return render_template('dash/profiles/profiles.html', **page_vars)


@dash.route('/profiles/new', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.profiles.new', 'New Profile')
def new_profile():
    """Render a form allowing the user to add a test profile."""

    form = NewProfileForm()

    if form.validate_on_submit():
        profile = Profile(name=form.name.data)
        sql.session.add(profile)
        sql.session.commit()

        flash('Profile successfully added.', 'success')
        return redirect(url_for('dash.profile', pid=profile.id))

    page_vars = {
        'title': 'New Profile',
        'navwell': True,
        'page_header': 'New Profile',
        'form': form
    }
    return render_template('dash/profiles/new-profile.html', **page_vars)


@dash.route('/profiles/<string:pid>/edit', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(dash, 'bc.dash.profiles.edit', 'Edit Profile')
def profile(pid):
    """Render a form to edit an existing profile."""
    profile = Profile.query.filter_by(id=pid).first()
    form = EditProfileForm()

    if form.validate_on_submit():
        profile.name = form.name.data
        sql.session.add(profile)
        sql.session.commit()

        flash('Changes saved.', 'success')
        return redirect(url_for('dash.profile', pid=pid))

    form.name.data = profile.name

    page_vars = {
        'title': 'Edit Profile',
        'sidebar_class': ' sidebar two-column' if profile.pushed else '',
        'sidebar_right': profile.pushed,
        'navwell': True,
        'page_header': 'Edit Profile',
        'form': form,
        'profile': profile
    }
    return render_template('dash/profiles/edit-profile.html', **page_vars)


@dash.route('/profiles/<string:pid>/delete')
@admin_required
@confirm_required(
    'Are you sure you want to delete this profile?',
    'I am sure', 'dash.profile', ['pid'], 'danger'
)
def delete_profile(pid):
    """Remove a profile from the database."""
    profile = Profile.query.filter_by(id=pid).first()
    sql.session.delete(profile)
    sql.session.commit()

    flash('Profile successfully deleted.', 'success')
    return redirect(url_for('dash.profiles'))


@dash.route('/profiles/<string:pid>/push')
@admin_required
@confirm_required(
    'Are you sure you want to push this profile to the recommender system?',
    'I am sure', 'dash.profile', ['pid'], 'danger'
)
def push_profile(pid):
    """ Push a profile to the recommender system.
        It will now be considered in recommendations for other profiles in
        a sandbox setting.
    """
    profile = mongo.db.profiles
    p = Profile.query.filter_by(id=pid).first()

    insert_result = profile.insert_one({
        'name': p.name,
        'external_id': p.id
    })

    # Save the id given to the profile by the recommender system.
    # Mark profile as being pushed to the recommender system.
    p.rs_id = str(insert_result.inserted_id)
    p.pushed = True
    sql.session.add(p)
    sql.session.commit()

    flash('Profile successfully pushed.', 'success')
    return redirect(url_for('dash.profile', pid=pid))


@dash.route('/profiles/<string:pid>/pull')
@admin_required
@confirm_required(
    'Are you sure you want to pull this profile from the recommender system?',
    'I am sure', 'dash.profile', ['pid'], 'danger'
)
def pull_profile(pid):
    """ Pull a profile from the recommender system.
        It will no longer be considered in recommendations for profiles.
    """
    profile = mongo.db.profiles
    p = Profile.query.filter_by(id=pid).first()

    # Delete profile.
    profile.delete_one({'_id': ObjectId(p.rs_id)})

    # Delete answers.
    answer = mongo.db.answers
    answers = [a['_id']
               for a in answer.find({'profile': ObjectId(p.rs_id)})]
    answer.delete_many({'_id': {'$in': answers}})

    # Clear pushed flag on profile.
    p.rs_id = None
    p.pushed = False
    sql.session.add(p)
    sql.session.commit()

    flash('Profile successfully pulled.', 'success')
    return redirect(url_for('dash.profile', pid=pid))

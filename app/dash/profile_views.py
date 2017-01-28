"""Implements dashboard endpoints."""


from flask import (
    flash, redirect, render_template, url_for,
)
from flask_breadcrumbs import register_breadcrumb


from app import sql
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
        'navwell': True,
        'page_header': 'Edit Profile',
        'form': form,
        'pid': pid
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

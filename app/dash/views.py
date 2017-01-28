"""Implements dashboard endpoints."""


from flask import (
    render_template,
)
from flask_breadcrumbs import register_breadcrumb


from app.dash import dash
from app.utils.decorators import admin_required


@dash.route('/')
@admin_required
@register_breadcrumb(dash, 'bc.dash', 'Management Dashboard')
def index():
    """Render index page."""
    page_vars = {
        'title': 'Management Dashboard',
        'navwell': True,
        'page_header': 'Management Dashboard'
    }
    return render_template('dash/index.html', **page_vars)

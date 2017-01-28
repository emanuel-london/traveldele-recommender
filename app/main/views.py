"""Implements main endpoints."""


from flask import render_template
from flask_breadcrumbs import register_breadcrumb


from app.main import main


@main.route('/')
@register_breadcrumb(main, 'bc.', 'Home')
def index():
    """Render index page."""
    page_vars = {
        'title': 'Home'
    }
    return render_template('main/index.html', **page_vars)
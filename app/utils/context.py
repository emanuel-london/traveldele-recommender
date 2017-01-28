"""Application context processors."""


from datetime import datetime


from flask import request

from app import app
from app.utils.models import Permission


@app.context_processor
def inject_permissions():
    """Make permissions available in all template files."""
    return dict(Permission=Permission)


@app.context_processor
def inject_date():
    return dict(date=datetime.now())


@app.context_processor
def inject_site_name():
    return dict(site_name=app.config['SITE_NAME'])


@app.context_processor
def inject_org_name():
    return dict(org_name=app.config['ORG_NAME'])


@app.context_processor
def inject_endpoint():
    return dict(endpoint=request.endpoint)

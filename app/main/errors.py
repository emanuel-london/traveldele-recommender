"""Implements error handlers used throughout the Flask app."""


from flask import (
    jsonify, make_response, render_template,
)


from . import main


@main.app_errorhandler(400)
def bad_request(dummy_err):
    """HTTP Bad Request"""
    return make_response(jsonify({'error': 'Bad Request.'}), 400)


@main.app_errorhandler(404)
def page_not_found(dummy_err):
    """HTTP Not Found."""
    page_vars = {
        'title': 'Page Not Found',
        'page_header': 'Not Found'
    }
    return render_template('error/404.html', **page_vars), 404


@main.app_errorhandler(405)
def method_not_allowed(dummy_err):
    """HTTP Method Not Allowed."""
    return make_response(jsonify({'error': 'Method not allowed.'}), 405)


@main.app_errorhandler(500)
def internal_server_error(dummy_err):
    """HTTP Internal Server Error."""
    page_vars = {
        'title': 'Internal Server Error',
        'page_header': 'Internal Server Error'
    }
    return render_template('error/500.html', **page_vars), 500
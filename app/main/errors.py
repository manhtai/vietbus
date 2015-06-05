from flask import render_template
from app.main import main


@main.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@main.app_errorhandler(429)
def too_many_requests(e):
    return render_template('errors/429.html'), 429

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500



"""Implements authentication ui endpoints."""


from flask import (
    flash, redirect, render_template,
    request, url_for,
)
from flask_login import (
    current_user, login_required,
    login_user, logout_user,
)
from itsdangerous import BadSignature


from app import sql
from app.auth import auth
from app.auth.forms import (
    LoginForm, PasswordForm, PasswordResetForm,
)
from app.utils.mail import send_mail
from app.utils.models import User


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Present user login form."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    login_form = LoginForm(prefix='login_form')

    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user is not None and user.verify_password(
                login_form.password.data):
            login_user(user, login_form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.', 'danger')

    page_vars = {
        'sidebar_right': True,
        'sidebar_class': ' two-column',
        'title': 'Sign in',
        'login_form': login_form
    }
    return render_template('auth/login.html', **page_vars)


@auth.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('main.index'))


@auth.route('/password', methods=['GET', 'POST'])
def password():
    """Present password reset form."""
    pass_form = PasswordForm()

    if pass_form.validate_on_submit():
        user = User.query.filter_by(email=pass_form.email.data).first()
        token = user.generate_security_token()
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        text = render_template('mail/password.txt', vars={
            'user': user,
            'reset_url': reset_url
        })
        html = render_template('mail/password.html', vars={
            'user': user,
            'reset_url': reset_url
        })
        subject = 'Password reset instructions.'
        send_mail(subject, recipients=[user.email], text=text, html=html)

        flash('Password reset instructions have been sent to {0}'
              .format(user.email), 'success')
        return redirect(url_for('auth.login'))

    page_vars = {
        'title': 'Reset Your Password',
        'page_header': 'Reset your password',
        'form': pass_form
    }
    return render_template('auth/password.html', **page_vars)


@auth.route('/password/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Corfirm password reset token."""
    try:
        email = User.confirm_password_reset_token(token)
    except BadSignature:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('main.index'))

    pass_form = PasswordResetForm(reset_token=token)

    if pass_form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user is not None:
            try:
                user.confirm_security_token(pass_form.reset_token.data)
            except BadSignature:
                flash('The password reset link is invalid or has expired.',
                      'danger')
                return redirect(url_for('main.index'))

            user.password = pass_form.password.data

            if not user.confirmed:
                user.confirmed = True

            sql.session.add(user)
            sql.session.commit()
            flash('Your password has been successfully reset. You can now \
                  login using your new password.', 'success')
            return redirect(url_for('auth.login'))

    page_vars = {
        'title': 'Set New Password',
        'page_header': 'Set your new password',
        'form': pass_form
    }
    return render_template('auth/new-password.html', **page_vars)

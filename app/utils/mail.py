"""Flask app mailing functions."""


__all__ = ['send_mail']


from flask_mail import Message


from app import app
from app import mailer
from app.utils.decorators import async


@async
def send_mail_async(msg):
    """Non-blocking mail sender."""
    with app.app_context():
        mailer.send(msg)


def send_mail(subject, recipients, sender=None, text='', html='', cc=None, reply_to=None, attachments=[]):
    """Construct message and send asynchronously."""
    msg = Message(subject, sender=sender,
                  recipients=recipients, reply_to=reply_to)

    if cc is not None and cc[0] is not None:
        msg.cc = cc

    for a in attachments:
        with app.open_resource(a['uri']) as fp:
            msg.attach(a['filename'], a['mimetype'], fp.read())

    msg.body = text
    msg.html = html
    send_mail_async(msg)

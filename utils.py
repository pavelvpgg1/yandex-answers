from flask import current_app
from flask_mail import Message


def send_confirm_email(user):
    from app import mail  # импортировать только внутри функции!
    token = user.get_confirm_token()
    msg = Message('Подтверждение почты для Яндекс Ответы',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    link = f"http://127.0.0.1:5000/confirm/{token}"
    msg.body = f"Привет! Для подтверждения регистрации перейди по ссылке: {link}"
    mail.send(msg)

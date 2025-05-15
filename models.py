from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rating = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='user')  # user/moderator/admin
    is_email_confirmed = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_confirm_token(self, expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_confirm_token(token, expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expires_sec)
        except Exception:
            return None
        return User.query.get(data['user_id'])


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())
    rating = db.Column(db.Integer, default=0)
    user = db.relationship('User', backref='questions')
    category = db.relationship('Category', backref='questions')


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    rating = db.Column(db.Integer, default=0)
    is_best = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='answers')
    question = db.relationship('Question', backref='answers')


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    object_id = db.Column(db.Integer)
    object_type = db.Column(db.String(20))  # 'question' или 'answer'
    is_like = db.Column(db.Boolean, default=True)  # True=лайк, False=дизлайк


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))

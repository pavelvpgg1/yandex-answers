from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired(), Email()])
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(2, 64)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')


class AskForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(), Length(5, 200)])
    body = TextAreaField('Текст вопроса', validators=[DataRequired(), Length(10)])
    category = SelectField('Категория', coerce=int)
    submit = SubmitField('Задать вопрос')


class AnswerForm(FlaskForm):
    body = TextAreaField('Ответ', validators=[DataRequired(), Length(5)])
    submit = SubmitField('Ответить')

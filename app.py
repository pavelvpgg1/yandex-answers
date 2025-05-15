from flask import Flask, render_template, redirect, url_for, flash
from flask import jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail

from api import api_bp
from forms import LoginForm, RegisterForm, AskForm, AnswerForm
from models import db, User, Question, Answer, Category, Like
from utils import send_confirm_email

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandex_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yandex_answers.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bogodpav@gmail.com'
app.config['MAIL_PASSWORD'] = 'nwyc fhwc wsvi krnm'

db.init_app(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

app.register_blueprint(api_bp, url_prefix='/api')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('index.html', questions=questions)


@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Нет доступа!')
        return redirect(url_for('index'))
    users = User.query.all()
    questions = Question.query.all()
    return render_template('admin.html', users=users, questions=questions)


@app.route('/make_admin/<int:user_id>', methods=['POST'])
@login_required
def make_admin(user_id):
    if current_user.role != 'admin':
        flash('Нет доступа!')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    flash('Пользователь теперь админ!')
    return redirect(url_for('admin_panel'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        send_confirm_email(user)
        flash('На почту отправлено письмо для подтверждения регистрации!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/confirm/<token>')
def confirm_email(token):
    user = User.verify_confirm_token(token)
    if not user:
        flash('Ссылка некорректна или устарела')
        return redirect(url_for('login'))
    user.is_email_confirmed = True
    db.session.commit()
    flash('Почта подтверждена. Теперь можно войти.')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_email_confirmed:
                flash('Сначала подтвердите почту!')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/ask', methods=['GET', 'POST'])
@login_required
def ask():
    form = AskForm()
    categories = Category.query.all()
    form.category.choices = [(c.id, c.name) for c in categories]
    if form.validate_on_submit():
        question = Question(title=form.title.data, body=form.body.data, user_id=current_user.id,
                            category_id=form.category.data)
        db.session.add(question)
        db.session.commit()
        flash('Вопрос добавлен!')
        return redirect(url_for('index'))
    return render_template('ask.html', form=form)


@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def question(question_id):
    question = Question.query.get_or_404(question_id)
    answers = Answer.query.filter_by(question_id=question.id).order_by(Answer.created_at).all()
    form = AnswerForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        answer = Answer(body=form.body.data, user_id=current_user.id, question_id=question.id)
        db.session.add(answer)
        db.session.commit()
        flash('Ответ опубликован!')
        return redirect(url_for('question', question_id=question.id))
    return render_template('question.html', question=question, answers=answers, form=form)


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    questions = Question.query.filter_by(user_id=user.id).all()
    answers = Answer.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', user=user, questions=questions, answers=answers)


@app.route('/category/<int:category_id>')
def category(category_id):
    cat = Category.query.get_or_404(category_id)
    questions = Question.query.filter_by(category_id=cat.id).all()
    return render_template('category.html', category=cat, questions=questions)


@app.route('/like/<object_type>/<int:object_id>/<action>', methods=['POST'])
@login_required
def like(object_type, object_id, action):
    is_like = (action == 'like')
    like = Like.query.filter_by(user_id=current_user.id, object_id=object_id, object_type=object_type).first()
    if like:
        # Если уже такой есть и то же действие — убираем лайк
        if like.is_like == is_like:
            db.session.delete(like)
        else:
            like.is_like = is_like
    else:
        like = Like(user_id=current_user.id, object_id=object_id, object_type=object_type, is_like=is_like)
        db.session.add(like)
    db.session.commit()

    # Пересчитать рейтинг
    likes = Like.query.filter_by(object_id=object_id, object_type=object_type, is_like=True).count()
    dislikes = Like.query.filter_by(object_id=object_id, object_type=object_type, is_like=False).count()

    # Сохраняем рейтинг в вопрос или ответ
    if object_type == 'question':
        obj = Question.query.get(object_id)
    else:
        obj = Answer.query.get(object_id)
    obj.rating = likes - dislikes
    db.session.commit()
    return jsonify({'likes': likes, 'dislikes': dislikes, 'rating': obj.rating})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Category.query.first():
            db.session.add(Category(name="Математика"))
            db.session.add(Category(name="Информатика"))
            db.session.add(Category(name="Физика"))
            db.session.add(Category(name="Литература"))
            db.session.commit()
    app.run(debug=True)

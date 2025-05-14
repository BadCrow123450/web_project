from flask import Flask, abort, url_for, make_response, session
from flask import request as req
from data import db_session
from data.users import User
from data.news import News
from flask import render_template
from forms.user import RegisterForm
from flask import redirect
from requests import request
from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired
from forms.news import NewsForm
import random


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/training', methods=['GET', 'POST'])
def training():
    if current_user.is_authenticated:
        return render_template("training.html", user_name=session['name'], age=session['age'],
                               sex=session['sex'],
                               height=session['height'], weight=session['weight'])
    else:
        return render_template("training.html", age=session['age'], sex=session['sex'],
                               height=session['height'], weight=session['weight'])


@app.route('/', methods=['GET', 'POST'])
def main():
    if current_user.is_authenticated:
        return render_template("main_menu.html", user_name=session['name'])
    else:
        return render_template("main_menu.html")


@app.route('/like/<int:id>', methods=['GET', 'POST'])
def like(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == str(id),
                                      ).first()
    if news:
        news.likes = str(int(news.likes) + 1)
        db_sess.commit()
    else:
        abort(404)
    return f'Ваше сообщение номер {id} было лайкнуто'


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/profile')


@app.route("/profile")
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private is not True)
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private is not True))
    else:
        news = db_sess.query(News).filter(News.is_private is not True)
    if current_user.is_authenticated:
        return render_template("index.html", user_name=session['name'], news=news)
    else:
        return render_template("index.html", news=news)


@app.route("/success")
def success():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == session['name']).first()
    user.rating = user.rating + 3
    db_sess.commit()
    return 'Вы молодец! Вы заработали 3 балла рейтина'


@app.route('/news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/profile')
    if current_user.is_authenticated:
        return render_template("news.html", user_name=session['name'], form=form)
    else:
        return render_template("news.html", form=form)


@app.route('/info',  methods=['GET', 'POST'])
def info():
    if current_user.is_authenticated:
        return render_template("info.html", user_name=session['name'])
    else:
        return render_template("info.html")


@app.route('/records',  methods=['GET', 'POST'])
def records():
    db_sess = db_session.create_session()
    users = db_sess.query(User)
    z = sorted([el for el in users], key=lambda x: -x.rating)
    if current_user.is_authenticated:
        return render_template("records.html", users=z, user_name=session['name'])
    else:
        return render_template("records.html", users=z)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if req.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/profile')
        else:
            abort(404)
    if current_user.is_authenticated:
        return render_template("news.html", user_name=session['name'], form=form)
    else:
        return render_template("news.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            session['name'] = form.email.data
            session['age'] = user.age
            session['weight'] = user.weight
            session['height'] = user.height
            session['sex'] = user.sex
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    if current_user.is_authenticated:
        return render_template("login.html", user_name=session['name'], form=form)
    else:
        return render_template("login.html", form=form)


@app.route('/missions', methods=['GET', 'POST'])
def missions():
    missions = ['Прыгнуть на скакалке 100 раз',
                'Отжаться 15 раз',
                'Подтянуться 5 раз',
                'Присесть 2 раза',
                'Принять душ',
                'Съесть мандарин',
                'Побегать',
                'Пройти 10 метров',
                'Попить протеиновый напиток',
                'Выйти на улицу',
                'Погулять в парке',
                'Сбегать до сарая',
                'Построить дом',
                'Посадить дерево',
                'Воспитать сына',
                'Поехать в лес',
                'Съездить в другую страну',
                'Сгибание локтей 12 раз',
                'Отдохнуть',
                'Выяснить смысл существования',
                'Съесть лимон',
                'Похудеть',
                'Лечь спать',
                'Подарить цветы маме',
                'Удалить компьюерную игру (доту)',
                'Скачать секундомер',
                'Выучить E=mc^2',
                'Выяснить почему так холодно',
                'Наладить режим сна',
                'Снять фильм',
                'Выбросить телефон',
                'Приготовить что-то полезное',
                'Полежать 5 минут',
                'Приготовить вещи для похода',
                'Остановить коррупцию',
                'Пресс 20 раз',
                'Написать программу на Python',
                'Приготовиться к открытию мероприятия',
                'Выключить компьютер',
                'Заняться делом', 'Открыть окно', 'Полюбоваться на виды из окна',
                'Помыть машину (любую)', 'Подбросить монетку', 'Прослушать любимую песню.']
    mission = random.choice(missions)
    if current_user.is_authenticated:
        return render_template("missions.html", user_name=session['name'], mission=mission)
    else:
        return render_template("missions.html", mission=mission)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            weight=form.weight.data,
            height=form.height.data,
            age=form.age.data,
            sex=form.sex.data,
            rating=0
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    if current_user.is_authenticated:
        return render_template("register.html", user_name=session['name'], form=form)
    else:
        return render_template("register.html", form=form)


def main():
    db_session.global_init("db/blogs.db")
    app.run(port=5000)
    session.permanent = True


if __name__ == '__main__':
    main()

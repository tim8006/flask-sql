from flask import Flask, redirect, render_template, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.users import User
from data.db_session import global_init, create_session
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField
from forms.user import RegisterForm
from data.jobs import Jobs
from data.departments import Department


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/')
def table():
    global_init("db/mars_explorer.db")
    db_sess = create_session()
    list_jobs = []
    for job in db_sess.query(Jobs).all():
        list_jobs.append({'id': job.id, 'title': job.job, 'leader': f'{job.user.name} {job.user.surname}',
                          'duration': job.work_size, 'list': job.collaborators, 'finish': job.is_finished,
                          'team_leader': job.team_leader, 'category': job.categories.id})
    return render_template('table.html', data=list_jobs)


@app.route('/departments')
def departments():
    global_init("db/mars_explorer.db")
    db_sess = create_session()
    list_departments = []
    for department in db_sess.query(Department).all():
        list_departments.append({'id': department.id, 'title': department.title,
                                 'chief': f'{department.boss.name} {department.boss.surname}',
                                 'members': department.members, 'email': department.email,
                                 'team_leader': department.chief})
    return render_template('departments.html', data=list_departments)


class DepartmentForm(FlaskForm):
    title = StringField('Department Title')
    chief = StringField('Chief id')
    members = StringField('Members')
    email = StringField('Email')
    submit = SubmitField('Submit')


@app.route('/add_departments',  methods=['GET', 'POST'])
@login_required
def add_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        db_sess = create_session()
        department = Department()
        department.title = form.title.data
        department.chief = form.chief.data
        department.members = form.members.data
        department.email = form.email.data
        current_user.departments.append(department)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/departments')
    return render_template('add_department.html', title='Adding a Department',
                           form=form)


@app.route('/departments/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_departments(id):
    form = DepartmentForm()
    if request.method == "GET":
        db_sess = create_session()
        department = db_sess.query(Department).filter(Department.id == id,
                                                      Department.chief == current_user.id).first()
        if department:
            form.title.data = department.title
            form.chief.data = department.chief
            form.members.data = department.members
            form.email.data = department.email
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = create_session()
        department = db_sess.query(Department).filter(Department.id == id,
                                                      Department.chief == current_user.id).first()
        if department:
            department.title = form.title.data
            department.chief = form.chief.data
            department.members = form.members.data
            department.email = form.email.data
            db_sess.commit()
            return redirect('/departments')
        else:
            abort(404)
    return render_template('add_department.html', title='Editing a Department', form=form)


@app.route('/departments_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def departments_delete(id):
    db_sess = create_session()
    department = db_sess.query(Department).filter(Department.id == id,
                                                  Department.chief == current_user.id).first()
    if department:
        db_sess.delete(department)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/departments')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        global_init('db/mars_explorer.db')
        db_sess = create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            surname=form.surname.data,
            name=form.name.data,
            email=form.email.data,
            age=form.age.data,
            position=form.position.data,
            speciality=form.speciality.data,
            address=form.address.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


class JobsForm(FlaskForm):
    job = StringField('Job Title')
    team_leader = StringField('Team Leader id')
    work_size = IntegerField('Work Size')
    collaborators = StringField('Collaborators')
    is_finished = BooleanField('Is job finished?')
    submit = SubmitField('Submit')


@app.route('/jobs',  methods=['GET', 'POST'])
@login_required
def add_job():
    form = JobsForm()
    if form.validate_on_submit():
        db_sess = create_session()
        jobs = Jobs()
        jobs.job = form.job.data
        jobs.team_leader = form.team_leader.data
        jobs.work_size = form.work_size.data
        jobs.collaborators = form.collaborators.data
        jobs.is_finished = form.is_finished.data
        current_user.jobs.append(jobs)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('jobs.html', title='Adding a Job',
                           form=form)


@app.route('/jobs/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = JobsForm()
    if request.method == "GET":
        db_sess = create_session()
        jobs = db_sess.query(Jobs).filter(Jobs.id == id,
                                          Jobs.team_leader == current_user.id
                                          ).first()
        if jobs:
            form.job.data = jobs.job
            form.team_leader.data = jobs.team_leader
            form.work_size.data = jobs.work_size
            form.collaborators.data = jobs.collaborators
            form.is_finished.data = jobs.is_finished
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = create_session()
        jobs = db_sess.query(Jobs).filter(Jobs.id == id,
                                          Jobs.team_leader == current_user.id
                                          ).first()
        if jobs:
            jobs.job = form.job.data
            jobs.team_leader = form.team_leader.data
            jobs.work_size = form.work_size.data
            jobs.collaborators = form.collaborators.data
            jobs.is_finished = form.is_finished.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('jobs.html',
                           title='Editing a Job',
                           form=form
                           )


@app.route('/jobs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = create_session()
    jobs = db_sess.query(Jobs).filter(Jobs.id == id,
                                      Jobs.team_leader == current_user.id
                                      ).first()
    if jobs:
        db_sess.delete(jobs)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        global_init("db/mars_explorer.db")
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')


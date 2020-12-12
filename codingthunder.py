# minimum app
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
import math
from werkzeug.utils import secure_filename


local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)['params']

app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_url']
app.config['SECRET_KEY'] = 'something only you know'
app.config['UPLOAD_FOLDER'] = params['img_db']
db = SQLAlchemy(app)


class Contacts(db.Model):
    __tablename__ = 'contacts'  # optional
    contactid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False)
    emailid = db.Column(db.String(45), nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    msg = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(45), nullable=False)

    def __init__(self, name, email, phone, msg, date):
        self.name = name
        self.emailid = email
        self.phone = phone
        self.msg = msg
        self.date = date


class Blogs(db.Model):
    __tablename__ = 'blogs'
    blogid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    creator = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(21), nullable=False)
    img_file = db.Column(db.String(12), nullable=True)

    def __init__(self ,title ,content ,creator ,date ,slug ,img_file):
        self.title=title
        self.content=content
        self.creator=creator
        self.date=date
        self.slug=slug
        self.img_file=img_file


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # if user already looged in
    if 'current_user' in session and session['current_user'] == params['username']:
        posts = Blogs.query.filter_by().all()
        return render_template('dashboard.html', params=params, posts=posts)

    # if user not logged in
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == params['username'] and password == params['password']:
            session['current_user']=params['username']
            posts = Blogs.query.filter_by().all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)


@app.route('/')
def home():
    print('enter')
    posts = Blogs.query.filter_by().all()
    last = math.ceil(len(posts)/params['nposts'])
    page = request.args.get('page')
    if not str(page).isnumeric():
        page=1
    page=int(page)
    posts = posts[ (page-1)*params['nposts'] : (page-1)*params['nposts']+params['nposts'] ]

    #pagination
    # first
    if page==1:
        prev='#'
        next='/?page='+str(page+1)
    # last
    elif page==last:
        prev='/?page='+str(page-1)
        next='#'
    # middle
    else:
        prev='/?page='+str(page-1)
        next='/?page='+str(page+1)
    print(prev,next)

    return render_template('index.html', params=params, posts=posts ,prev=prev ,next=next)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/post')
def sample_post():
    return render_template('sample_post.html', params=params)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post(post_slug):
    post = Blogs.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route('/edit/<string:blog_id>', methods=['GET', 'POST'])
def edit(blog_id):
    if 'current_user' in session and session['current_user'] == params['username']:
        if request.method=='POST':
            title = request.form['title']
            content= request.form['content']
            img_file = request.form['img_file']
            slug=title.strip().replace('?','').replace(' ','-')

            if blog_id=='0':
                print('am i coming?')
                post = Blogs(title ,content ,params['username'] ,datetime.now() ,slug ,img_file)
                db.session.add(post)
                db.session.commit()
                return redirect('/dashboard')
            else:
                post = Blogs.query.filter_by(blogid=blog_id).first()
                post.title = title
                post.slug = slug
                post.content=content
                post.img_file=img_file

                db.session.commit()
                return redirect('/dashboard')

        post = Blogs.query.filter_by(blogid=blog_id).first()
        return render_template('edit.html', params=params, post=post)
    else:
        return redirect('/dashboard')


@app.route('/delete/<string:blog_id>', methods=['GET', 'POST'])
def delete(blog_id):
    if 'current_user' in session and session['current_user'] == params['username']:
        post = Blogs.query.filter_by(blogid=blog_id).first()
        db.session.delete(post)
        db.engine.execute('SET @count := 0; UPDATE blogs SET blogs.blogid = @count:= (@count + 1);')
        db.session.commit()
    return redirect('/dashboard')


@app.route('/uploader' ,methods=['GET','POST'])
def uploader():
    if 'current_user' in session and session['current_user'] == params['username']:
        if request.method=='POST':
            f = request.files['img']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'] ,secure_filename(f.filename)))
            return 'uploaded successfully...'


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form['email']
        phone = request.form['phone']
        msg = request.form['msg']

        try:
            if not name or not email or not phone or not msg:
                flash('data is incomplete...! please fill all', 'error')
            else:
                # entry = Contacts(name=name ,emailid=email ,phone=phone ,msg=msg ,date=datetime.now())
                entry = Contacts(name, email, phone, msg, datetime.now())
                db.session.add(entry)
                db.session.commit()

                mail.send_message(name + ' try to connect with you...',
                                  sender=email,
                                  recipients=[params['gmail_user']],
                                  body=msg + '\n\n\nName:- ' + name + '\nGmail ID:- ' + email + '\nPhone no.:- ' + phone + '\nInformed at:- ' + datetime.now()
                                  )

                return redirect(url_for('home'))
        except:
            flash('data is incomplete...! please fill all', 'error')

    return render_template('contact.html', params=params)

@app.route('/logout')
def logout():
    session.pop('current_user',None)
    return redirect('/')


app.run(debug=True)
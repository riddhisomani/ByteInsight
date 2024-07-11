from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math
from datetime import datetime

with open('templates/config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = "True"
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = params['upload_location']

# mail configuration
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = params['gmail_username']
# app.config['MAIL_PASSWORD'] = params['gmail_pass']
# app.config['MAIL_USE_SSL'] = True

# mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_no = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12))
    email = db.Column(db.String(25), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    subheading = db.Column(db.String(50), nullable = False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable = True)
    img_file = db.Column(db.String(12), nullable = True)

@app.route('/')
def home(): 
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    # slicing of posts 
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    # first page
    if(page == 1):
        prev = '#'
        next = '/?page=' + str(page+1)
    elif(page == last):
        prev = '/?page=' + str(page-1)
        next = '#'
    else:
        prev = '/?page=' + str(page-1)
        next = '/?page=' + str(page+1)
    # posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html', params = params, posts = posts, prev = prev, next = next)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts = posts)
    if request.method == 'POST':
        # redirect to admin panel
        username = request.form.get('uname')
        userpass = request.form.get('paas')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params = params, posts = posts)
    else:
        return render_template('login.html', params = params)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html', params = params, post = post)

@app.route('/about')
def about():
    return render_template('about.html', params = params)

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            slug = request.form.get('slug')
            tagline = request.form.get('tline')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, slug=slug, subheading=tagline, content=content, img_file=img_file, date = date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = box_title
                post.slug = slug
                post.subheading = tagline
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
            return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post = post, sno = sno)

@app.route('/delete/<string:sno>', methods = ['GET', 'POST'])
def delete_post(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')

    
@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "File Uploaded"

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/login')

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('message')
        entry = Contact(name=name, phone_no=phone, message=msg, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from Blog', 
        #                   sender = email, 
        #                   recipients = [params['gmail_username']], 
        #                   body = msg + "\n" + phone
        #                   )
    return render_template('contact.html', params = params)

if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.run(debug=True, port = 8080)

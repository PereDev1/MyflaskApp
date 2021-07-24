from flask import Flask, render_template, request, flash, redirect, url_for, session, logging, g
from functools import wraps
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_ckeditor import CKEditorField
from passlib.hash import sha256_crypt

app = Flask(__name__)

#config MySql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'PereDev'
app.config['MYSQL_PASSWORD'] = 'perez1'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#initialize MySql
mysql = MySQL(app)

# Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    #create cursor
    cur = mysql.connection.cursor()

    #get article
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result>0:
        return render_template('articles.html', articles=articles)
    else:
        msg= 'No articles Found'
        return render_template('articles.html', msg=msg)

    #close the connection
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message= 'Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data))

            #create cursor
            cur = mysql.connection.cursor()

            cur.execute("INSERT INTO users(name, email,username, password) VALUES(%s,%s,%s,%s)", (name, email, username, password))

            #Commit to DB
            mysql.connection.commit()

            #close the connection
            cur.close()

            flash('You are now registeres and can log in', 'success')

            return redirect(url_for('login'))
    return render_template('register.html', form=form)

#user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result>0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #compare password
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # close connection
            cur.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        flash('Unaouthorized, Please log in', 'danger')
        return redirect(url_for('login'))
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #get article
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result>0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg= 'No articles Found'
        return render_template('dashboard.html', msg=msg)

    #close the connection
    cur.close()


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = CKEditorField('Body', [validators.Length(min=25)])

@app.route('/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    form = ArticleForm(request.form)
    
    if request.method =='POST' and form.validate():
        title = form.title.data
        body = form.body.data
        
        #create Cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES (%s,%s,%s)", (title, body, session['username']))

        #commit
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

#edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    # create cursor 
    cur = mysql.connection.cursor()

    #get the article by id
    result = cur.execute("SELECT * FROM articles WHERE id= %s", [id])

    article = cur.fetchone()

    #get form
    form = ArticleForm(request.form)

    # populate article form fields 
    form.title.data = article['title']
    form.body.data = article['body']
    
    if request.method =='POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        
        #create Cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("UPDATE articles SET title= %s, body=%s WHERE id=%s", (title,body,id))

        #commit
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article updated', 'success')

        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

#delete article
@app.route('/delete_article/<string:id>', methods= ['POST'])
@login_required
def delete_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM articles WHERE id=%s", [id])

    #commmit to DB
    mysql.connection.commit()

    #close connection
    cur.close()

    flash('Article deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key= 'secret123'
    app.run(debug=True)
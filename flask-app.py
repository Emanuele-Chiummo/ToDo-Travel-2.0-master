import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for, send_from_directory

from flask_avatars import Avatars


def connection_db():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

def register_user_to_db(username,first_name, last_name, email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('INSERT INTO users(username, first_name, last_name, email, password) values (?,?,?,?,?)', (username, first_name, last_name, email, password))
    con.commit()
    con.close()


def check_user(username, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('Select username,password FROM users WHERE username=? and password=?', (username, password))

    result = cur.fetchone()
    if result:
        return True
    else:
        return False

app = Flask(__name__)
avatars = Avatars(app)
app.secret_key = "r@nd0mSk_1"

@app.route("/")
def index():
    return render_template('login.html')


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        register_user_to_db(username, first_name, last_name, email, password)
        return redirect(url_for('index'))

    else:
        return render_template('register.html')


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(check_user(username, password))
        if check_user(username, password):
            session['username'] = username

        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))


@app.route('/home', methods=['POST', "GET"])
def home():

    if 'username' in session:
        connection = connection_db()
        posts = connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        return render_template('home.html', username=session['username'], posts=posts)
    else:
        return "Username or Password is wrong!"
        
    
@app.route('/<int:idx>/delete', methods=('POST',))
def delete(idx):
    connection = connection_db()
    connection.execute('DELETE FROM posts WHERE id=?', (idx,))
    connection.commit()
    connection.close()
    return redirect('/home')

@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        info = request.form['info']
        connection = connection_db()
        connection.execute(
            'INSERT INTO posts (title, info) VALUES (?, ?)', (title, info,))
        connection.commit()
        connection.close()
        return redirect('/home')
    return render_template('create.html')

@app.route('/<int:idx>/edit', methods=('GET', 'POST'))
def edit(idx):
    connection = connection_db()
    posts = connection.execute(
        'SELECT * from posts where id=?', (idx,)).fetchone()
    connection.close()

    if request.method == 'POST':
        title = request.form['title']
        info = request.form['info']
        connection = connection_db()
        connection.execute(
            'UPDATE posts SET title=?, info=? WHERE id=?', (title, info, idx))
        connection.commit()
        connection.close()
        return redirect('/home')
    return render_template('edit.html', posts=posts)
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/<username>/edit-profile', methods=('GET', 'POST'))
def edit_profile(username):
    connection = connection_db()
    users = connection.execute(
        'SELECT * from users where username=?', (session['username'],)).fetchone()
    connection.close()

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        connection = connection_db()
        connection.execute(
            'UPDATE users SET first_name=?, last_name=?, email=? WHERE username=?', (first_name, last_name, email, username))
        connection.commit()
        connection.close()
        return redirect('/home')
    return render_template('edit-profile.html', users=users)



if __name__ == '__main__':
    app.run(debug=True)

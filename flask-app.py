import sqlite3
from flask import Flask, redirect, flash, render_template, request, session, url_for, send_from_directory, make_response
from werkzeug.utils import secure_filename
from flask_avatars import Avatars
from authlib.integrations.flask_client import OAuth
import os



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
oauth = OAuth(app)
avatars = Avatars(app)
app.secret_key = os.urandom(12)

@app.route("/")
def index():
    return render_template('login.html')

@app.route('/google/')
def google():

    GOOGLE_CLIENT_ID = ''
    GOOGLE_CLIENT_SECRET = ''
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    # Redirect to google_auth function
    redirect_uri = url_for('google_auth', _external=True)
    print(redirect_uri)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    user = oauth.google.parse_id_token(token)
    session['username'] = token['userinfo']
    print(" Google User ", user)
    return redirect('/home')

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
    connection.execute('DELETE FROM travel WHERE id=?', (idx,))
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

@app.route('/viaggio', methods=('GET', 'POST'))
def viaggio():
    if request.method == 'POST':
        viaggio = request.form['viaggio']
        destinazione = request.form['destinazione']
        data_partenza = request.form['data_partenza']
        data_ritorno = request.form['data_ritorno']
        soggiorno = request.form['soggiorno']
        nome_struttura = request.form['nome_struttura']
        indirizzo_struttura = request.form['indirizzo_struttura']
        viaggiattore = session['username']
        connection = connection_db()
        connection.execute(
            'INSERT INTO travel (viaggio, destinazione, viaggiatore, data_partenza, data_ritorno,soggiorno, nome_struttura, indirizzo_struttura) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ', (viaggio, destinazione, viaggiattore, data_partenza, data_ritorno, soggiorno, nome_struttura, indirizzo_struttura,))
        connection.execute('INSERT INTO my_travel (viaggio, destinazione, viaggiatore, data_partenza, data_ritorno) VALUES (?, ?, ?, ?, ?)', (viaggio, destinazione, viaggiattore, data_partenza, data_ritorno,))
        connection.commit()
        connection.close()
        return redirect('/home')
    return render_template('viaggio.html')

@app.route('/my-travel', methods=('GET', 'POST'))
def read():
    connection = connection_db()
    travel = connection.execute('SELECT * from travel where viaggiatore=?', (session['username'],)).fetchall()
    connection.commit()
    connection.close()
    return render_template('my-travel.html', username=session['username'], travel=travel)

@app.route('/soggiorno', methods=('GET', 'POST'))
def soggiorno():
    connection = connection_db()
    travel = connection.execute('SELECT * FROM travel').fetchall()
    connection.close()
    if request.method =='POST':
        soggiorno = request.form['soggiorno']
        nome_struttura = request.form['nome_struttura']
        indirizzo_struttura = request.form['indirizzo_struttura']
        connection = connection_db()
        connection.execute('UPDATE travel SET soggiorno=?, nome_struttura=?, indirizzo_struttura =?', (soggiorno,nome_struttura,indirizzo_struttura,))
        connection.commit()
        connection.close()
    return render_template('soggiorno.html', travel=travel)

@app.route('/travel', methods=('GET', 'POST'))
def travel():
    connection = connection_db()
    travel = connection.execute('SELECT * from travel where viaggiatore=?', (session['username'],)).fetchall()
    connection.commit()
    connection.close()
    return render_template('travel.html', username=session['username'], travel=travel)

@app.route('/<int:idx>/edit', methods=('GET', 'POST'))
def edit(idx):
    connection = connection_db()
    travel = connection.execute(
        'SELECT * from travel where id=?', (idx,)).fetchone()
    connection.close()

    if request.method == 'POST':
        destinazione = request.form['destinazione']
        data_partenza = request.form['data_partenza']
        data_ritorno = request.form['data_ritorno']
        soggiorno = request.form['soggiorno']
        nome_struttura = request.form['nome_struttura']
        indirizzo_struttura = request.form['indirizzo_struttura']
        connection = connection_db()
        connection.execute(
            'UPDATE travel SET destinazione=?, data_partenza = ?, data_ritorno = ?, soggiorno = ?, nome_struttura = ?, indirizzo_struttura = ? WHERE id=?', (destinazione,data_partenza,data_ritorno,soggiorno,nome_struttura, indirizzo_struttura, idx,))
        connection.commit()
        connection.close()
        return redirect('/home')
    return render_template('edit.html', travel=travel)

@app.route('/diario', methods=('GET', 'POST'))
def diario_insert():
    connection = connection_db()
    diario = connection.execute('SELECT * from diario').fetchall()
    connection.close()

    if request.method =='POST':
        titolo = request.form['titolo']
        info = request.form['info']
        connection = connection_db()
        connection.execute ('INSERT INTO diario (titolo, info) VALUES (?, ?)',(titolo, info,))
        connection.commit()
        connection.close()
        return redirect('/home')
    return render_template('diario.html', diario=diario)

@app.route('/<int:idx>/edit_post', methods=('GET', 'POST'))
def edit_post(idx):
    connection = connection_db()
    diario = connection.execute(
        'SELECT * from diario where id_diario=?', (idx,)).fetchone()
    connection.close()

    if request.method == 'POST':
        titolo = request.form['titolo']
        info = request.form['info']
        connection = connection_db()
        connection.execute(
            'UPDATE diario SET titolo=?, info=? WHERE id_diario = ?', (titolo, info, idx,))
        connection.commit()
        connection.close()
        return redirect('/home')
    return render_template('edit_post.html', diario=diario)

@app.route('/<int:idx>/delete_post', methods=('POST',))
def delete_post(idx):
    connection = connection_db()
    connection.execute('DELETE FROM diario WHERE id_diario =? ', (idx,))
    connection.commit()
    connection.close()
    return redirect('/home')

@app.route('/itinerario', methods=('GET', 'POST'))
def itinerario():

    return render_template('itinerario.html')   

@app.route('/amsterdam')
def Amsterdam():

    return render_template('Amsterdam.html')

if __name__ == '__main__':
    app.run(debug=True)

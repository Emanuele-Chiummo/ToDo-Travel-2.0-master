import sqlite3
from flask import Flask, redirect, flash, render_template, request, session, url_for, send_from_directory, make_response, abort
from werkzeug.utils import secure_filename
from flask_avatars import Avatars
from authlib.integrations.flask_client import OAuth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import os
import pathlib
import requests


def connection_db():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection


class School:
    def __init__(self, key, name, lat, lng):
        self.key = key
        self.name = name
        self.lat = lat
        self.lng = lng


schools = (
    School('Amsterdam',      'Amsterdam',   52.377956,  4.897070),
    School('Roma', 'Roma',            41.902782, 12.496366),
    School('Londra', 'Londra', 51.500153, -0.1262362)
)
schools_by_key = {school.key: school for school in schools}


def register_user_to_db(username, first_name, last_name, email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('INSERT INTO users(username, first_name, last_name, email, password) values (?,?,?,?,?)',
                (username, first_name, last_name, email, password))
    con.commit()
    con.close()


def check_user(username, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute(
        'Select username,password FROM users WHERE username=? and password=?', (username, password))

    




def reset_password(email):
    connection = connection_db()
    connection.cursor()
    connection.execute('Select email FROM users')


app = Flask(__name__)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
avatars = Avatars(app)
app.secret_key = os.urandom(12)

GOOGLE_CLIENT_ID = "488676761730-68ctqg40lld125augmqetekltsbr6r8a.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

@app.route("/login_google")
def login_google():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session['username'] = id_info.get("name")
    session['name'] = id_info.get('given_name')
    session['last_name'] = id_info.get('family_name')
    session['email'] = id_info.get("email")
    session['photo'] = id_info.get("picture")


    connection=connection_db()
    cur = connection.cursor()
    res = cur.execute('SELECT email FROM users where email=?',[session['email']],)


    if res.fetchone():
        
        return redirect("/home")
    else:
        connection.execute('INSERT INTO users (username, email, first_name, last_name) VALUES (?, ?, ?, ?)',(session['username'], session['email'],session['name'],session['last_name'], ))
        connection.commit()
        connection.close()

        return redirect("/home")


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


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/home', methods=['POST', "GET"])

def home():

    if 'username' in session: #cambiato name in username
        connection = connection_db()
        posts = connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        return render_template('home.html', username=session['username'], posts=posts) #cambiato name in username
    else:
        return redirect('/not_found')
   


@app.route('/<int:idx>/delete', methods=('POST',))
def delete(idx):
    if 'username' in session:
        connection = connection_db()
        connection.execute('DELETE FROM travel WHERE id=?', (idx,))
        connection.commit()
        connection.close()
        return redirect('/home')
    else:
        return redirect('/not_found')


@app.route('/create', methods=('GET', 'POST'))
def create():
    if 'username' in session:
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
    else:
        return redirect('/not_found')


@app.route('/<username>/edit-profile', methods=('GET', 'POST'))
def edit_profile(username):
    if 'username' in session:
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
    else:
        return redirect('/not_found')


@app.route('/viaggio', methods=('GET', 'POST'))
def viaggio():

    if 'username' in session:
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
            connection.execute('INSERT INTO my_travel (viaggio, destinazione, viaggiatore, data_partenza, data_ritorno) VALUES (?, ?, ?, ?, ?)',
                           (viaggio, destinazione, viaggiattore, data_partenza, data_ritorno,))
            connection.commit()
            connection.close()
            return redirect('/home')

        return render_template('viaggio.html')
    else:
        return redirect('/not_found')


@app.route('/my-travel', methods=('GET', 'POST'))
def read():
    if 'username' in session:
        connection = connection_db()
        travel = connection.execute(
        'SELECT * from travel where viaggiatore=?', (session['username'],)).fetchall()
        connection.commit()
        connection.close()
        return render_template('my-travel.html', username=session['username'], travel=travel)
    else:
        return redirect('/not_found')


@app.route('/soggiorno', methods=('GET', 'POST'))
def soggiorno():
    if 'username' in session:
        connection = connection_db()
        travel = connection.execute('SELECT * FROM travel').fetchall()
        connection.close()
        if request.method == 'POST':
            soggiorno = request.form['soggiorno']
            nome_struttura = request.form['nome_struttura']
            indirizzo_struttura = request.form['indirizzo_struttura']
            connection = connection_db()
            connection.execute('UPDATE travel SET soggiorno=?, nome_struttura=?, indirizzo_struttura =?',
                           (soggiorno, nome_struttura, indirizzo_struttura,))
            connection.commit()
            connection.close()
        return render_template('soggiorno.html', travel=travel)
    else:
        return redirect('/not_found')


@app.route('/travel', methods=('GET', 'POST'))
def travel():
    if 'username' in session:
        connection = connection_db()
        travel = connection.execute(
        'SELECT * from travel where viaggiatore=?', (session['username'],)).fetchall()
        connection.commit()
        connection.close()
        return render_template('travel.html', username=session['username'], travel=travel)
    else:
        return redirect('/not_found')


@app.route('/<int:idx>/edit', methods=('GET', 'POST'))
def edit(idx):
    if 'username' in session:
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
            'UPDATE travel SET destinazione=?, data_partenza = ?, data_ritorno = ?, soggiorno = ?, nome_struttura = ?, indirizzo_struttura = ? WHERE id=?', (destinazione, data_partenza, data_ritorno, soggiorno, nome_struttura, indirizzo_struttura, idx,))
            connection.commit()
            connection.close()
            return redirect('/home')
        return render_template('edit.html', travel=travel)
    else:
        return redirect('/not_found')


@app.route('/diario', methods=('GET', 'POST'))
def diario_insert():
    if 'username' in session:
        connection = connection_db()
        diario = connection.execute(
        'SELECT * from diario where viaggiatore =?', (session['username'],)).fetchall()
        connection.close()

        if request.method == 'POST':
            titolo = request.form['titolo']
            info = request.form['info']
            viaggiatore = session['username']
            connection = connection_db()
            connection.execute(
            'INSERT INTO diario (titolo, info, viaggiatore) VALUES (?, ?, ?)', (titolo, info, viaggiatore,))
            connection.commit()
            connection.close()
            return redirect('/home')
        return render_template('diario.html', username=session['username'], diario=diario)
    else:
        return redirect('/not_found')


@app.route('/<int:idx>/edit_post', methods=('GET', 'POST'))
def edit_post(idx):
    if 'username' in session:
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
    else:
        return redirect('/not_found')


@app.route('/<int:idx>/delete_post', methods=('POST',))
def delete_post(idx):
    if 'username' in session:
        connection = connection_db()
        connection.execute('DELETE FROM diario WHERE id_diario =? ', (idx,))
        connection.commit()
        connection.close()
        return redirect('/home')
    else:
        return redirect('/not_found')


@app.route('/itinerario', methods=('GET', 'POST'))
def itinerario():
    if 'username' in session:

        return render_template('itinerario.html', itinerario=itinerario)
    else:
        return redirect('/not_found')


@app.route('/new_itinerario', methods=('GET', 'POST'))
def new_itinerario():
    if 'username' in session:

        if request.method == 'POST':
            citta = request.form['citta']
            paese = request.form['paese']
            viaggiatore = session['username']
            itinerario = request.form['itinerario']
            connection = connection_db()
            connection.execute('INSERT INTO itinerario (citta, paese, itinerario, viaggiatore) VALUES (?, ?, ?, ?)',
                           (citta, paese, itinerario, viaggiatore,))
            connection.commit()
            connection.close()
            return redirect('/home')

        return render_template('new_itinerario.html')
    else:
        return redirect('/not_found')


@app.route('/your_itinerari', methods=('GET', 'POST'))
def your_itinerari():
    if 'username' in session:
        connection = connection_db()
        itinerario = connection.execute(
        'SELECT * from itinerario where viaggiatore=?', (session['username'],)).fetchall()
        connection.commit()
        connection.close()
        return render_template('your_itinerari.html', username=session['username'], itinerario=itinerario)
    else:
        return redirect('/not_found')


@app.route('/<int:idx>/edit_itinerario', methods=('GET', 'POST'))
def edit_itinerario(idx):
    if 'username' in session:
        connection = connection_db()
        itinerario = connection.execute(
        'SELECT * from itinerario where id_itinerario=?', (idx,)).fetchone()
        connection.close()

        if request.method == 'POST':
            citta = request.form['citta']
            paese = request.form['paese']
            itinerario = request.form['itinerario']
            connection = connection_db()
            connection.execute(
            'UPDATE itinerario SET citta=?, paese=?, itinerario =? WHERE id_itinerario = ?', (citta, paese, itinerario, idx,))
            connection.commit()
            connection.close()
            return redirect('/home')
        return render_template('edit_itinerario.html', itinerario=itinerario)
    else:
        return redirect('/not_found')


@app.route('/<int:idx>/delete_itinerario', methods=('POST',))
def delete_itinerario(idx):
    if 'username' in session:
        connection = connection_db()
        connection.execute(
        'DELETE FROM itinerario WHERE id_itinerario =? ', (idx,))
        connection.commit()
        connection.close()
        return redirect('/home')
    else:
        return redirect('/not_found')


@app.route('/amsterdam')
def Amsterdam():
    if 'username' in session:
        return render_template('Amsterdam.html')
    else:
        return redirect('/not_found')


@app.route('/bagaglio', methods=('GET', 'POST'))
def bagaglio():
    if 'username' in session:
        connection = connection_db()
        bagaglio = connection.execute(
        'SELECT * from bagaglio where viaggiatore =?', (session['username'],)).fetchall()
        connection.close()

        if request.method == 'POST':
            memo = request.form['memo']
            viaggiatore = session['username']
            connection = connection_db()
            connection.execute(
            'INSERT INTO bagaglio (memo, viaggiatore) VALUES (?, ?)', (memo, viaggiatore,))
            connection.commit()
            connection.close()
            return redirect('/bagaglio')

        return render_template('bagaglio.html', bagaglio=bagaglio)
    else:
        return redirect('/not_found')


@app.route('/<int:idx>/delete_memo', methods=('POST',))
def delete_bagaglio(idx):
    if 'username' in session:
        connection = connection_db()
        connection.execute('DELETE FROM bagaglio WHERE id_bagaglio =? ', (idx,))
        connection.commit()
        connection.close()
        return redirect('/bagaglio')
    else:
        return redirect('/not_found')


@app.route("/trasporti")
def trasporti():
    if 'username' in session:

        return render_template('trasporti.html', schools=schools)
    else:
        return redirect('/not_found')


@app.route("/<school_code>")
def show_school(school_code):
    if 'username' in session:
        school = schools_by_key.get(school_code)
        if school:
            return render_template('map.html', school=school)
        else:
            abort(404)
    else:
        return redirect('/not_found')

@app.route('/not_found')
def not_found():

    return render_template('not_found.html')


if __name__ == '__main__':
    app.run(debug=True)

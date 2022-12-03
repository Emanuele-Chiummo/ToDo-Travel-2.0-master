DROP TABLE IF EXISTS posts;

CREATE TABLE posts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    info TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    
);

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id INTEGER Primary KEY AUTOINCREMENT,
    username Text not null,
    first_name TEXT not null,
    last_name TEXT not null,
    email TEXT not null,
    password TEXT not null
);

DROP TABLE IF EXISTS travel;
CREATE TABLE travel(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    viaggiatore REFERENCES users(username),
    destinazione REFERENCES my_travel(destinazione), 
    data_partenza REFERENCES my_travel(data_partenza), 
    data_ritorno REFERENCES my_travel(data_ritorno), 
    viaggio REFERENCES my_travel(viaggio), 
    hotel REFERENCES my_travel(soggiorno),
    soggiorno TEXT,
    nome_struttura TEXT, 
    indirizzo_struttura TEXT
);

DROP TABLE IF EXISTS my_travel;
CREATE TABLE my_travel(
    travel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    viaggiatore REFERENCES users(username),
    destinazione TEXT,
    data_partenza DATETIME,
    data_ritorno DATETIME, 
    viaggio TEXT, 
    soggiorno TEXT,
    nome_struttura TEXT, 
    indirizzo_struttura TEXT
);

DROP TABLE IF EXISTS diario;
CREATE TABLE diario(
    id_diario INTEGER PRIMARY KEY AUTOINCREMENT,
    viaggiatore REFERENCES users(username),
    titolo TEXT NOT NULL, 
    info TEXT NOT NULL,
    destinazione TEXT,
    immagine BLOB, 
    FOREIGN KEY (id_diario) REFERENCES travel(id)
    ON UPDATE CASCADE
);
DROP TABLE IF EXISTS itinerario;
CREATE TABLE itinerario(
    id_itinerario INTEGER PRIMARY KEY AUTOINCREMENT,
    viaggiatore REFERENCES users(username),
    citta TEXT NOT NULL,
    paese TEXT, 
    itinerario TEXT 
);

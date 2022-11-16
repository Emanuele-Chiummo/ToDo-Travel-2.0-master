DROP TABLE IF EXISTS posts;

CREATE TABLE posts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    info TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    
);


CREATE TABLE users (
    user_id INTEGER Primary KEY AUTOINCREMENT,
    username Text not null,
    first_name TEXT not null,
    last_name TEXT not null,
    email TEXT not null,
    password TEXT not null
);

CREATE TABLE travel(
    viaggiatore REFERENCES users(username),
    travel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    destinazione TEXT, 
    data_partenza DATETIME, 
    data_ritorno DATETIME, 
    viaggio TEXT not null, 
    hotel TEXt
);
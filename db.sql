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
    username Text not null ,
    first_name TEXT not null,
    last_name TEXT not null,
    email TEXT not null,
    password TEXT not null
);
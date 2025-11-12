import sqlite3
conn = sqlite3.connect('data/db.sqlite3')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR UNIQUE NOT NULL,
    user_id VARCHAR NOT NULL,
    agent_id INTEGER,
    name VARCHAR,
    description VARCHAR,
    status VARCHAR DEFAULT 'active',
    is_active BOOLEAN DEFAULT 1,
    container_id VARCHAR,
    container_status VARCHAR,
    base_url VARCHAR,
    auth_data VARCHAR,
    environment_vars VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (agent_id) REFERENCES agents (id)
)''')
conn.commit()
print('Sessions table created successfully!')
conn.close()
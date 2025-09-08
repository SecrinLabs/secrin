-- create user table
CREATE TABLE users (
    id SERIAL PRIMARY KEY, -- auto-incrementing user ID
    email VARCHAR(255) UNIQUE NOT NULL, -- unique email
    username VARCHAR(50) UNIQUE, -- optional username
    password_hash TEXT NOT NULL, -- store hashed password, not plaintext
    github_installation_id BIGINT -- GitHub App installation_id
);
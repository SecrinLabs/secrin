-- create repository table
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY, -- auto-incrementing repository ID
    user_id INT NOT NULL, -- FK to users.id
    repo_name VARCHAR(255) NOT NULL, -- repository name
    repo_url VARCHAR(255) NOT NULL, -- repository URL
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT unique_user_repo UNIQUE (user_id, repo_url)
);

-- optional index for faster lookups
CREATE INDEX idx_repositories_user_id ON repositories (user_id);
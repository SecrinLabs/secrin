-- create github commit table
CREATE TABLE githubcommits (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    sha VARCHAR(64) UNIQUE NOT NULL,
    message TEXT,
    author_name TEXT,
    author_email TEXT,
    author_date TIMESTAMPTZ,
    committer_name TEXT,
    committer_email TEXT,
    committer_date TIMESTAMPTZ,
    html_url TEXT,
    raw_payload JSONB, -- keep full JSON from GitHub for flexibility
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);

-- create commit files table
CREATE TABLE githubcommitfiles (
    id SERIAL PRIMARY KEY,
    commit_sha VARCHAR(64) NOT NULL REFERENCES githubcommits (sha) ON DELETE CASCADE,
    filename TEXT,
    status TEXT, -- added / modified / removed
    additions INT,
    deletions INT,
    changes INT,
    patch TEXT
);
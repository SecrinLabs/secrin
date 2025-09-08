-- alter repositories table to add GitHub metadata columns
ALTER TABLE repositories
ADD COLUMN repo_id BIGINT, -- GitHub's repository id
ADD COLUMN full_name TEXT, -- owner/name
ADD COLUMN description TEXT,
ADD COLUMN private BOOLEAN,
ADD COLUMN language VARCHAR(50),
ADD COLUMN topics TEXT [], -- tags (array of text)
ADD COLUMN stargazers_count INT,
ADD COLUMN forks_count INT,
ADD COLUMN watchers_count INT,
ADD COLUMN default_branch VARCHAR(50),
ADD COLUMN open_issues_count INT,
ADD COLUMN has_issues BOOLEAN,
ADD COLUMN has_discussions BOOLEAN,
ADD COLUMN archived BOOLEAN,
ADD COLUMN created_at TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP,
ADD COLUMN pushed_at TIMESTAMP,
ADD COLUMN clone_url TEXT,
ADD COLUMN owner_login VARCHAR(100),
ADD COLUMN owner_type VARCHAR(20);
-- First create the enum type
CREATE TYPE integration_type AS ENUM ('github');

-- Then create the table
CREATE TABLE integration (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    type integration_type NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'
);
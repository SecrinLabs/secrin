CREATE TABLE IF NOT EXISTS integrations (
  id SERIAL primary KEY,
  name TEXT UNIQUE NOT NULL,
  is_connected BOOLEAN DEFAULT FALSE,
  config JSONB DEFAULT '{}' 
)
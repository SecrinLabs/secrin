-- Make password_hash nullable
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- Add status column if not exists
ALTER TABLE users
ADD COLUMN IF NOT EXISTS status SMALLINT NOT NULL DEFAULT 0;
-- status meaning:
-- 0 = pending (user invited but password not set)
-- 1 = active (user has set password and can login)
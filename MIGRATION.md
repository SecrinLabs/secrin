# DevSecrin Migration Guide

This guide helps you migrate from development setup to production, or upgrade from older versions.

## 📋 Migration Scenarios

### 1. Development to Production

#### Prerequisites
- Docker and Docker Compose installed
- SSL certificates (for HTTPS)
- Domain name configured
- Backup strategy in place

#### Steps

1. **Backup your data:**
   ```bash
   # Backup database
   pg_dump -h localhost -U devsecrin devsecrin > backup.sql
   
   # Backup vector database
   tar -czf chroma_backup.tar.gz chroma_store/
   
   # Backup configuration
   cp .env .env.backup
   ```

2. **Update configuration for production:**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

3. **Deploy with Docker:**
   ```bash
   # Use production configuration
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

4. **Restore data:**
   ```bash
   # Restore database
   docker-compose exec postgres psql -U devsecrin -d devsecrin < backup.sql
   
   # Restore vector database
   tar -xzf chroma_backup.tar.gz
   ```

### 2. Upgrading from Previous Versions

#### From v0.1.x to v1.0.x

1. **Stop the current version:**
   ```bash
   docker-compose down
   ```

2. **Backup current data:**
   ```bash
   ./deploy.sh --backup-only
   ```

3. **Pull latest code:**
   ```bash
   git pull origin main
   ```

4. **Update dependencies:**
   ```bash
   docker-compose pull
   ```

5. **Run migrations:**
   ```bash
   docker-compose run --rm devsecrin python packages/dbup/runner.py
   ```

6. **Start updated version:**
   ```bash
   docker-compose up -d
   ```

### 3. Environment-Specific Migrations

#### Local Development → Docker

1. **Export current data:**
   ```bash
   # Export database
   python -c "
   from packages.db.db import engine
   from sqlalchemy import text
   import json
   
   with engine.connect() as conn:
       # Export integrations
       result = conn.execute(text('SELECT * FROM integrations'))
       integrations = [dict(row) for row in result]
       
       with open('integrations_export.json', 'w') as f:
           json.dump(integrations, f, default=str)
   "
   ```

2. **Setup Docker environment:**
   ```bash
   docker-compose up -d
   ```

3. **Import data:**
   ```bash
   # Import integrations
   python -c "
   import json
   from packages.db.db import engine
   from sqlalchemy import text
   
   with open('integrations_export.json', 'r') as f:
       integrations = json.load(f)
   
   with engine.connect() as conn:
       for integration in integrations:
           conn.execute(text('''
               INSERT INTO integrations (name, type, config, created_at, updated_at)
               VALUES (:name, :type, :config, :created_at, :updated_at)
               ON CONFLICT (name) DO UPDATE SET
                   config = EXCLUDED.config,
                   updated_at = EXCLUDED.updated_at
           '''), integration)
       conn.commit()
   "
   ```

## 🔧 Configuration Migration

### Database Configuration Changes

#### Old Format (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost/db
```

#### New Format (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost/db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=db
DATABASE_USER=user
DATABASE_PASSWORD=pass
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### API Configuration Changes

#### Old Format
```env
API_HOST=localhost
API_PORT=8000
```

#### New Format
```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
API_KEY=your_api_key_here
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
RATE_LIMIT_PER_MINUTE=60
```

### AI Model Configuration Changes

#### Old Format
```env
OLLAMA_HOST=localhost:11434
```

#### New Format
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_GPU_LAYERS=35
MAX_TOKENS=2048
TEMPERATURE=0.7
```

## 🗄️ Database Schema Migrations

### Migration Scripts

Create database migration scripts in `packages/dbup/sql/`:

#### Add new columns
```sql
-- 2025_01_15_add_user_preferences.sql
ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';
CREATE INDEX idx_users_preferences ON users USING GIN (preferences);
```

#### Update existing data
```sql
-- 2025_01_15_update_integration_config.sql
UPDATE integrations 
SET config = config || '{"version": "1.0.0"}'::jsonb
WHERE config->>'version' IS NULL;
```

### Running Migrations

```bash
# Automatic migration
python packages/dbup/runner.py

# Manual migration
python packages/dbup/runner.py --file=2025_01_15_add_user_preferences.sql
```

## 🔄 Data Migration Utilities

### Export/Import Scripts

#### Export Configuration
```python
#!/usr/bin/env python3
"""Export DevSecrin configuration"""

import json
import os
from packages.config import get_config

def export_config():
    config = get_config()
    config_dict = config.to_dict()
    
    # Remove sensitive data
    sensitive_keys = ['github_token', 'confluence_api_token', 'database_password']
    for key in sensitive_keys:
        if key in config_dict:
            del config_dict[key]
    
    with open('config_export.json', 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    print("Configuration exported to config_export.json")

if __name__ == "__main__":
    export_config()
```

#### Import Configuration
```python
#!/usr/bin/env python3
"""Import DevSecrin configuration"""

import json
import os

def import_config():
    with open('config_export.json', 'r') as f:
        config_dict = json.load(f)
    
    # Convert to environment variables
    env_content = "# Imported DevSecrin Configuration\n\n"
    for key, value in config_dict.items():
        env_key = key.upper()
        env_content += f"{env_key}={value}\n"
    
    with open('.env.imported', 'w') as f:
        f.write(env_content)
    
    print("Configuration imported to .env.imported")
    print("Please review and merge with your .env file")

if __name__ == "__main__":
    import_config()
```

## 🛠️ Troubleshooting Common Migration Issues

### Database Connection Issues

**Problem:** Database connection fails after migration
**Solution:**
```bash
# Check database status
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database if needed
docker-compose down
docker volume rm devsecrin_postgres_data
docker-compose up -d
```

### Vector Database Issues

**Problem:** ChromaDB data is lost or corrupted
**Solution:**
```bash
# Backup existing data
tar -czf chroma_backup.tar.gz chroma_store/

# Clear vector database
rm -rf chroma_store/

# Rebuild embeddings
python -c "
from packages.ai.newindex import run_graph_embedder
run_graph_embedder()
"
```

### Model Loading Issues

**Problem:** Ollama model not found after migration
**Solution:**
```bash
# Check available models
docker-compose exec ollama ollama list

# Pull required model
docker-compose exec ollama ollama pull deepseek-r1:1.5b

# Restart services
docker-compose restart
```

### Configuration Issues

**Problem:** Environment variables not loading
**Solution:**
```bash
# Check .env file exists
ls -la .env

# Validate configuration
python test_system.py

# Check for syntax errors
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Environment loaded successfully')
"
```

## 🚀 Production Deployment Checklist

### Pre-deployment

- [ ] Backup all data
- [ ] Test migration in staging environment
- [ ] Update DNS records
- [ ] Prepare SSL certificates
- [ ] Configure monitoring
- [ ] Set up log rotation
- [ ] Configure backups

### During Deployment

- [ ] Put maintenance page up
- [ ] Stop old services
- [ ] Deploy new version
- [ ] Run database migrations
- [ ] Update AI models
- [ ] Start new services
- [ ] Verify health checks
- [ ] Remove maintenance page

### Post-deployment

- [ ] Monitor application logs
- [ ] Check performance metrics
- [ ] Verify all integrations work
- [ ] Test key functionality
- [ ] Update documentation
- [ ] Notify team of completion

## 📞 Getting Help

### Migration Support

If you encounter issues during migration:

1. **Check logs:**
   ```bash
   docker-compose logs --tail=100
   ```

2. **Run system tests:**
   ```bash
   python test_system.py
   ```

3. **Create GitHub issue** with:
   - Migration scenario
   - Error messages
   - System configuration
   - Steps to reproduce

### Community Support

- **GitHub Issues**: Report bugs and get help
- **Documentation**: Check INSTALL.md and README.md
- **Examples**: Look at example configurations in the repo

## 🔄 Rollback Procedures

### Quick Rollback

```bash
# Stop current version
docker-compose down

# Restore from backup
docker-compose exec postgres psql -U devsecrin -d devsecrin < backup.sql

# Start previous version
git checkout previous-version-tag
docker-compose up -d
```

### Full Rollback

```bash
# Complete rollback script
./deploy.sh --rollback
```

This will restore:
- Database from latest backup
- Configuration from backup
- Vector database from backup
- Previous Docker images

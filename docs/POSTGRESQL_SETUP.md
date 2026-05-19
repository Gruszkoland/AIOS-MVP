# PostgreSQL Setup Guide — ADRION 369 v1.0

## Opcje konfiguracji

### Opcja 1: SQLite (Najprościej — Zalecane dla DEV)

SQLite jest już skonfigurowany jako fallback. Brak dodatkowej konfiguracji potrzebnej.

```bash
# .env
DB_ENGINE=sqlite
SQLITE_DB_PATH=./arbitrage.db
```

**Zalety:**
- Brak instalacji
- Lokalny plik (./arbitrage.db)
- Wystarczająco dla testowania

**Wady:**
- Niska wydajność dla dużych danych
- Brak współbieżności
- Brak multi-tenant isolation

---

### Opcja 2: PostgreSQL Lokalnie (Windows)

#### Krok 1: Instalacja PostgreSQL

Pobierz z: https://www.postgresql.org/download/windows/

```bash
# Wybierz podczas instalacji:
- Version: 15.x
- Install pgAdmin: Yes (optional)
- Port: 5432
- Password: <silne hasło>
```

#### Krok 2: Utwórz bazę danych

```bash
# Windows PowerShell lub Git Bash
psql -U postgres

# W psql:
CREATE USER adrion WITH PASSWORD 'strong_password_here';
CREATE DATABASE genesis_record OWNER adrion;
GRANT ALL PRIVILEGES ON DATABASE genesis_record TO adrion;
\q
```

#### Krok 3: Konfiguruj .env

```bash
# .env
DB_ENGINE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_USER=adrion
PG_PASSWORD=strong_password_here
PG_DB=genesis_record

# Lub pełny connection string:
DATABASE_URL=postgresql://adrion:strong_password_here@localhost:5432/genesis_record
```

#### Krok 4: Uruchom backend

```bash
cd uap/backend
export PG_HOST=localhost
export PG_USER=adrion
export PG_PASSWORD=strong_password_here
python api.py
```

**Logs powinny pokazać:**
```
✅ PostgreSQL connected successfully
```

---

### Opcja 3: PostgreSQL w Docker (Zalecane dla PROD)

#### Krok 1: Zainstaluj Docker Desktop

Pobierz z: https://www.docker.com/products/docker-desktop

#### Krok 2: Uruchom PostgreSQL kontener

```bash
docker run -d \
  --name adrion-postgres \
  -e POSTGRES_USER=adrion \
  -e POSTGRES_PASSWORD=strong_password \
  -e POSTGRES_DB=genesis_record \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine
```

#### Krok 3: Konfiguruj .env

```bash
# .env
DB_ENGINE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_USER=adrion
PG_PASSWORD=strong_password
PG_DB=genesis_record
```

#### Krok 4: Uruchom docker-compose (all-in-one)

```bash
docker-compose up -d

# Czekaj na health checks
docker-compose ps
```

---

## Weryfikacja conexji

### Test 1: Bezpośrednie połączenie

```bash
# Instaluj psql command-line tool
# Windows: https://www.postgresql.org/download/windows/

psql -h localhost -U adrion -d genesis_record -c "SELECT version();"
```

Oczekiwany wynik:
```
PostgreSQL 15.x on...
```

### Test 2: Za pośrednictwem backendu

```bash
curl -H "X-API-Key: local-dev-key-123" \
     http://localhost:8002/mapi/v1/status
```

Powinno zwrócić JSON z DB metrics.

### Test 3: pgAdmin (jeśli Docker)

```
http://localhost:5050
Email: admin@example.com
Password: admin
```

Add server:
- Host: postgres (lub localhost)
- Port: 5432
- User: adrion
- Password: <twoje_hasło>

---

## Migracje bazy danych

### Automatyczne migracje (Alembic)

```bash
# Install alembic
pip install alembic

# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### Manualne schematy (już zaimplementowane w db.py)

db.py zawiera _init_schema() które automatycznie tworzy tabele:

```python
- tasks
- genesis_logs
- checkpoints
- agent_metrics
```

---

## PRIORITY 1: PostgreSQL Integration w ADRION 369

### Backend Configuration

`uap/backend/db.py` zawiera:

```python
class PostgresDB:
    def __init__(self):
        self.conn_string = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        self._init_schema()  # Auto-create tables

    def _init_schema(self):
        # CREATE TABLE IF NOT EXISTS tasks
        # CREATE TABLE IF NOT EXISTS genesis_logs
        # CREATE TABLE IF NOT EXISTS checkpoints
        # CREATE TABLE IF NOT EXISTS agent_metrics
```

### Fallback to SQLite/In-Memory

`uap/backend/api.py` zawiera:

```python
try:
    db = PostgresDB()  # Try PostgreSQL
    USE_DATABASE = True
except Exception as e:
    logger.warning(f"PostgreSQL failed: {e}. Using in-memory.")
    db = None
    USE_DATABASE = False
```

**Rezultat:**
- ✅ PostgreSQL dostępny: Persystentna baza danych
- ✅ PostgreSQL niedostępny: Fallback do in-memory (dane tracone na restart)

---

## Backup & Restore

### Backup PostgreSQL

```bash
# Full backup
pg_dump -h localhost -U adrion genesis_record > genesis_record_backup.sql

# Compressed backup
pg_dump -h localhost -U adrion genesis_record | gzip > genesis_record_backup.sql.gz
```

### Restore z backup

```bash
psql -h localhost -U adrion genesis_record < genesis_record_backup.sql
```

---

## Troubleshooting

### Connection refused

```
Error: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Rozwiązanie:**
```bash
# PostgreSQL running?
netstat -an | grep 5432

# Start PostgreSQL service (Windows)
net start postgresql-x64-15

# Or use pgAdmin GUI to start
```

### Permission denied

```
Error: FATAL: password authentication failed for user "adrion"
```

**Rozwiązanie:**
```bash
# Verify credentials
psql -U postgres  # Login as admin first
\du  # List users

# Reset password
ALTER USER adrion WITH PASSWORD 'new_password';
```

### Database already exists

```
ERROR: database "genesis_record" already exists
```

**Rozwiązanie:**
```bash
# Drop and recreate
psql -U postgres
DROP DATABASE IF EXISTS genesis_record;
CREATE DATABASE genesis_record OWNER adrion;
```

---

## Production Recommendations

1. **Use PostgreSQL** (not SQLite)
   - Better concurrency
   - Better performance
   - Better security

2. **Enable SSL/TLS**
   ```
   sslmode=require
   ```

3. **Set strong password**
   - Min 32 characters
   - Mix of upper, lower, digits, symbols

4. **Enable backups**
   - Daily automated backups
   - Off-site storage
   - 30-day retention

5. **Monitor**
   - Connection pool exhaustion
   - Slow queries
   - Disk space usage
   - Lock conflicts

6. **Maintenance**
   - VACUUM ANALYZE weekly
   - Index optimization
   - Statistics update

---

## Next Steps

```bash
# 1. Choose option (1, 2, or 3)
# 2. Configure .env with DB credentials
# 3. Verify connection
# 4. Run tests
# 5. Start backend

python uap/backend/api.py
```

✅ See logs for "✅ PostgreSQL connected successfully"

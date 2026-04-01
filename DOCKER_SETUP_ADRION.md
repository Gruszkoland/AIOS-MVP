# Setup Lokalnego Roju ADRION 369 (Docker)

Ten przewodnik pozwoli Ci postawić fundament pod autonomiczny system marketingu Google Maps na Twoim Windowsie przy użyciu Docker Desktop.

## 1. Struktura folderów
Uruchom w PowerShell:
```powershell
mkdir adrion-swarm; cd adrion-swarm
mkdir n8n_data
```

## 2. Plik docker-compose.yml
Utwórz plik `docker-compose.yml` w folderze `adrion-swarm`:

```yaml
version: '3.8'

services:
  # Serce Orkiestracji (SAP/Chronos)
  n8n:
    image: n8nio/n8n:latest
    container_name: adrion-n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=TWOJE_HASLO_TU
      - WEBHOOK_URL=http://localhost:5678/
    volumes:
      - ./n8n_data:/home/node/.n8n

  # Silnik Inteligencji (Librarian/Auditor)
  ollama:
    image: ollama/ollama:latest
    container_name: adrion-ollama
    restart: always
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_data:/root/.ollama
    # Odkomentuj poniższe, jeśli masz kartę NVIDIA
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # Baza Pamięci (Genesis Record)
  postgres:
    image: postgres:15
    container_name: adrion-db
    restart: always
    environment:
      - POSTGRES_USER=adrion
      - POSTGRES_PASSWORD=adrion_pass
      - POSTGRES_DB=genesis_record
    ports:
      - "5432:5432"
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
```

## 3. Uruchomienie
W terminalu (w folderze `adrion-swarm`):
```powershell
docker-compose up -d
```

## 4. Konfiguracja Modelu
Pobierz model LLAMA3 do lokalnych audytów:
```powershell
docker exec -it adrion-ollama ollama pull llama3
```

## 5. Dostęp:
- **n8n:** [http://localhost:5678](http://localhost:5678)
- **Ollama API:** [http://localhost:11434](http://localhost:11434)
- **Postgres:** localhost:5432 (User: adrion)

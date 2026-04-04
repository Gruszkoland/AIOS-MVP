# ⚡ ADRION 369 Kubernetes — 15 Minute Quick Start

**Goal:** Get everything running in 15 minutes
**Status:** Ready to execute

---

## 🎯 TERAZ - Klikaj po kolei:

### ✅ Krok 1: Enable K8s w Docker Desktop (2 min)

1. Otwórz **Docker Desktop**
2. Kliknij **Settings** ⚙️
3. Idź na **Kubernetes**
4. Zaznacz **Enable Kubernetes**
5. Kliknij **Apply & Restart**
6. ☕ Czekaj 2-3 minuty

### ✅ Krok 2: Deploy Kubernetes (copy-paste do PowerShell/Terminal)

```bash
cd "C:\Users\adiha\162 demencje w schemacie 369"
kubectl apply -f kubernetes/*.yaml
```

### ✅ Krok 3: Czekaj aż wszystko będzie gotowe

```bash
kubectl get pods -n adrion --watch
```

Czekaj aż wszystkie będą `Running`:
- postgres-0 ✅
- uap-backend (3x) ✅
- uap-frontend (2x) ✅
- pgadmin ✅

**Ctrl+C** aby wyjść

### ✅ Krok 4: Test Backend (otwórz nowy terminal)

```bash
kubectl port-forward -n adrion svc/uap-backend 8002:8002 &
curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status
```

**Oczekiwany rezultat:** JSON ze statusem ✅

### ✅ Krok 5: Test Frontend (otwórz nowy terminal)

```bash
kubectl port-forward -n adrion svc/uap-frontend 8003:8003 &
curl http://localhost:8003
```

**Oczekiwany rezultat:** HTML content ✅

---

## 🎮 Teraz instalujesz VS Code Extension

### ✅ Krok 1: Build extension

```bash
cd "C:\Users\adiha\162 demencje w schemacie 369\vscode-extension-adrion"
npm install
npm run compile
npm install -g @vscode/vsce
vsce package
```

### ✅ Krok 2: Install w VS Code

1. Otwórz **VS Code**
2. Kliknij **Extensions** (Ctrl+Shift+X)
3. Wpisz: `Install from VSIX...`
4. Wybierz: `adrion-369-extension-2.0.0.vsix`
5. Kliknij **Install**
6. **Reload** VS Code

### ✅ Krok 3: Sprawdź extension

1. Powinno być **ADRION 369** w Activity Bar (lewym pasku)
2. Kliknij na niego
3. Widzisz **Swarm Dashboard** z przyciskami

---

## 🎯 Co możesz robić teraz z extensionem:

| Co chcesz? | Przycisk |
|-----------|----------|
| Zobaczyć wszystkie poddy | 📊 List Pods |
| Zobaczyć logi backendu | 📝 Backend Logs (Live) |
| Dostać się do frontendu | 🔀 Port Forward Frontend |
| Dostać się do API | 🔀 Port Forward Backend |
| Restartować backend | 🔄 Restart Backend Pods |
| Skalować do 5 replik | 📈 Scale Backend (5 replicas) |
| Query do bazy danych | 🗄️ Query Database |
| Zobaczyć status HPA | 📈 HPA Status |

---

## 📋 Troubleshooting

### Docker Desktop K8s nie startuje?
```bash
# Sprawdź czy Kubernetes jest enabled w Docker Desktop settings
# Jeśli nie, włącz i czekaj 3 minuty

# Sprawdź status:
kubectl cluster-info
```

### Poddy nie startują?
```bash
# Sprawdź co jest nie tak:
kubectl describe pod postgres-0 -n adrion

# Sprawdź logi:
kubectl logs postgres-0 -n adrion
```

### Extension nie ładuje się?
1. Sprawdź: Extensions → ADRION 369 (powinno być "Installed")
2. Reload VS Code: Ctrl+Shift+P → "Reload Window"
3. Spróbuj jeszcze raz

### Port forward się zamyka?
Dodaj `&` na koniec, aby działał w tle:
```bash
kubectl port-forward svc/uap-backend 8002:8002 &
```

---

## 🎉 Co masz teraz?

✅ Kubernetes running locally
✅ 3 backend instances (auto-scaling)
✅ 2 frontend instances
✅ PostgreSQL z 50GB storage
✅ pgAdmin do zarządzania bazą
✅ VS Code extension do kontroli

---

## 📊 Następne kroki (opcjonalnie):

1. **Load testing** — Symuluj traffic i zobacz auto-scaling
2. **Monitoring** — Zainstaluj Prometheus + Grafana
3. **Cloud deployment** — Wrzuć na AWS/GCP/Azure

---

**Gotowe! Teraz masz pełny Kubernetes system lokalnie! 🚀**

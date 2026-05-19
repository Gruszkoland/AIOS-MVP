# 🎨 ADRION-369 Visualizations & Diagrams

**Dokument:** Visual Architecture & Dependency Diagrams  
**Data:** 14.05.2026  
**Format:** Mermaid.js  

---

## 1️⃣ MCP Services Dependency Graph

```mermaid
graph TB
    Client["👤 Client<br/>(External)"]
    Router["🔀 MCP Router<br/>(Port 8000)<br/>Central Hub"]
    
    subgraph Genesis["🌅 Genesis Layer"]
        GM["genesis-mcp<br/>(Port 8001)<br/>11.8 KB<br/>Initialize System"]
    end
    
    subgraph Guardian["🛡️ Guardian Layer"]
        GD["guardian-mcp<br/>(Port 8002)<br/>9.7 KB<br/>Validate & Secure"]
    end
    
    subgraph Healer["💊 Healer Layer"]
        HL["healer-mcp<br/>(Port 8003)<br/>8.9 KB<br/>Detect & Repair"]
    end
    
    subgraph Oracle["🔮 Oracle Layer"]
        OC["oracle-mcp<br/>(Port 8004)<br/>8.7 KB<br/>Predict & Analyze"]
    end
    
    subgraph Vortex["⚡ Vortex Layer"]
        VX["vortex-mcp<br/>(Port 8005)<br/>6.7 KB<br/>Process & Stream"]
    end
    
    subgraph Infrastructure["🏗️ Infrastructure"]
        DB["PostgreSQL<br/>(State & Audit)"]
        Cache["Redis<br/>(Cache Layer)"]
        Queue["RabbitMQ<br/>(Events)"]
    end
    
    Client -->|HTTP/REST| Router
    Router -->|Route /genesis| GM
    Router -->|Route /guardian| GD
    Router -->|Route /healer| HL
    Router -->|Route /oracle| OC
    Router -->|Route /vortex| VX
    
    GM -->|Init Data| GD
    GM -->|State| Cache
    GM -->|Logs| DB
    
    GD -->|Validate| HL
    GD -->|Rules| Cache
    GD -->|Audit| DB
    
    HL -->|Proposals| OC
    HL -->|State| VX
    HL -->|Events| Queue
    
    OC -->|Predictions| VX
    OC -->|Model| Cache
    OC -->|Metrics| DB
    
    VX -->|Processed Data| GM
    VX -->|Stream| Queue
    VX -->|Results| Cache
    
    style Client fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style Router fill:#ff6b9d,stroke:#c4065d,stroke-width:3px
    style GM fill:#4ecdc4,stroke:#1a9b8e,stroke-width:2px
    style GD fill:#ffe66d,stroke:#ffb700,stroke-width:2px
    style HL fill:#95e1d3,stroke:#5ab89a,stroke-width:2px
    style OC fill:#f38181,stroke:#e24545,stroke-width:2px
    style VX fill:#aa96da,stroke:#7469d8,stroke-width:2px
    style DB fill:#c5e1a5,stroke:#7cb342,stroke-width:2px
    style Cache fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style Queue fill:#b2dfdb,stroke:#00695c,stroke-width:2px
```

---

## 2️⃣ Request Flow Through Pipeline

```mermaid
sequenceDiagram
    participant User as User/Client
    participant R as Router:8000
    participant G as Genesis:8001
    participant Gd as Guardian:8002
    participant H as Healer:8003
    participant O as Oracle:8004
    participant V as Vortex:8005
    participant DB as PostgreSQL
    participant Cache as Redis
    
    User->>R: POST /api/v1/process
    activate R
    
    R->>G: /genesis/init
    activate G
    G->>DB: Load state
    G->>Cache: Store init state
    G-->>R: State created ✓
    deactivate G
    
    R->>Gd: /guardian/validate
    activate Gd
    Gd->>DB: Check policies
    Gd->>Cache: Verify permissions
    Gd-->>R: Valid ✓
    deactivate Gd
    
    R->>O: /oracle/predict
    activate O
    O->>Cache: Load ML model
    O->>O: Process features
    O-->>R: Predictions ready
    deactivate O
    
    R->>H: /healer/detect
    activate H
    H->>O: Check anomalies
    H->>DB: Generate proposals
    H-->>R: Healed ✓
    deactivate H
    
    R->>V: /vortex/process
    activate V
    V->>Cache: Get enriched data
    V->>V: Process stream
    V-->>R: Results ready
    deactivate V
    
    R-->>User: 200 OK + Results
    deactivate R
    
    Note over User,Cache: Total latency: ~600ms (p95)
```

---

## 3️⃣ Deployment Architecture

```mermaid
graph TD
    subgraph Local["💻 Local Development"]
        L["docker-compose.local.yml"]
        LD["Single Node<br/>All Services<br/>Shared Network"]
    end
    
    subgraph Staging["🏗️ Staging Environment"]
        S["Kubernetes Cluster"]
        SN1["Node 1<br/>2 replicas"]
        SN2["Node 2<br/>2 replicas"]
        SN3["Node 3<br/>1 replica"]
        SDB["RDS PostgreSQL"]
        SElastiCache["ElastiCache Redis"]
    end
    
    subgraph Prod["🏢 Production Environment"]
        P["Kubernetes Cluster<br/>Auto-scaling"]
        PN1["Node 1<br/>3 replicas"]
        PN2["Node 2<br/>3 replicas"]
        PN3["Node 3<br/>3 replicas"]
        PN4["Node 4<br/>2 replicas"]
        PDB["RDS PostgreSQL<br/>(HA + Backup)"]
        PElastiCache["ElastiCache Redis<br/>(Cluster)"]
        PLB["AWS Load Balancer"]
        PWG["WAF/Security"]
    end
    
    L --> LD
    S --> SN1
    S --> SN2
    S --> SN3
    SN1 --- SDB
    SN2 --- SElastiCache
    
    P --> PN1
    P --> PN2
    P --> PN3
    P --> PN4
    PLB --> P
    PWG --> PLB
    PN1 --- PDB
    PN2 --- PElastiCache
    
    style Local fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style Staging fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Prod fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    style LD fill:#c8e6c9
    style S fill:#ffe0b2
    style P fill:#ffccbc
```

---

## 4️⃣ Test Coverage Distribution

```mermaid
pie title Test Coverage by Module (Target: 80%)
    "genesis_mcp (85%)" : 85
    "guardian_mcp (78%)" : 78
    "vortex_mcp (71%)" : 71
    "router (76%)" : 76
    "healer_mcp (68%)" : 68
    "oracle_mcp (64%)" : 64
    "core (58%)" : 58
    "arbitrage (52%)" : 52
    "dashboard (45%)" : 45
    "frontend (62%)" : 62
```

---

## 5️⃣ Code Complexity Heatmap

```mermaid
graph LR
    A["oracle_mcp<br/>CC: 28<br/>🔴 CRITICAL"] --> B["healer_mcp<br/>CC: 22<br/>🔴 HIGH"]
    B --> C["vortex_mcp<br/>CC: 19<br/>🟡 MEDIUM"]
    C --> D["guardian_mcp<br/>CC: 18<br/>🟡 MEDIUM"]
    D --> E["genesis_mcp<br/>CC: 12<br/>🟡 MEDIUM"]
    E --> F["router<br/>CC: 14<br/>🟡 MEDIUM"]
    
    style A fill:#ff6b6b,color:#fff,stroke:#c92a2a,stroke-width:3px
    style B fill:#ff8787,color:#fff,stroke:#e03131,stroke-width:2px
    style C fill:#ffd43b,color:#333,stroke:#f59f00,stroke-width:2px
    style D fill:#ffd43b,color:#333,stroke:#f59f00,stroke-width:2px
    style E fill:#ffd43b,color:#333,stroke:#f59f00,stroke-width:2px
    style F fill:#ffd43b,color:#333,stroke:#f59f00,stroke-width:2px
```

---

## 6️⃣ Performance Metrics Timeline

```mermaid
xychart-beta
    title Performance Optimization Roadmap
    x-axis [Jun, Jul, Aug, Sep, Oct, Nov]
    y-axis "Latency (ms)" 0 --> 700
    
    line [600, 550, 480, 420, 350, 280]
    
    scatter [
        [0, 600],
        [1, 550],
        [2, 480],
        [3, 420],
        [4, 350],
        [5, 280]
    ]
```

---

## 7️⃣ Technical Debt Burndown

```mermaid
xychart-beta
    title Technical Debt Reduction (Target: <100 hours)
    x-axis [Now, Week2, Week4, Month2, Month3]
    y-axis "Hours" 0 --> 160
    
    line [145, 130, 110, 85, 65]
    
    scatter [
        [0, 145],
        [1, 130],
        [2, 110],
        [3, 85],
        [4, 65]
    ]
```

---

## 8️⃣ Security Issues Status

```mermaid
pie title Security Issues by Severity
    "Critical (2)" : 2
    "High (3)" : 3
    "Medium (5)" : 5
    "Low (12)" : 12
```

---

## 9️⃣ Database Query Execution Flow

```mermaid
graph TB
    Query["SQL Query"]
    Parse["Parse & Validate"]
    Plan["Query Planner"]
    Execute["Execute"]
    Cache{"Cache<br/>Check"}
    Result["Results"]
    
    Query --> Parse
    Parse --> Plan
    Plan --> Execute
    Execute --> Cache
    Cache -->|Hit| Result
    Cache -->|Miss| Result
    
    style Cache fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
```

---

## 🔟 Service Health Status Matrix

```mermaid
graph TB
    subgraph Health["Health Status Dashboard"]
        G["🟢 Genesis<br/>Healthy<br/>✅ DB: OK<br/>✅ Cache: OK<br/>✅ CPU: 45%"]
        Gd["🟢 Guardian<br/>Healthy<br/>✅ DB: OK<br/>✅ Policies: OK<br/>✅ CPU: 62%"]
        H["🟡 Healer<br/>Degraded<br/>✅ DB: OK<br/>⚠️ CPU: 85%<br/>📈 Latency: 240ms"]
        O["🔴 Oracle<br/>Warning<br/>⚠️ Memory: 380MB<br/>⚠️ CPU: 92%<br/>⚠️ Latency: 680ms"]
        V["🟢 Vortex<br/>Healthy<br/>✅ Queue: OK<br/>✅ CPU: 72%<br/>✅ Throughput: 4200 req/s"]
    end
    
    style G fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Gd fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style H fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style O fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style V fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
```

---

## 1️⃣1️⃣ Data Flow Architecture

```mermaid
graph LR
    Source["📊 Data Source"]
    Ingest["Ingest<br/>(Vortex)"]
    Transform["Transform<br/>(Feature Eng)"]
    Enrich["Enrich<br/>(Oracle)"]
    Validate["Validate<br/>(Guardian)"]
    Store["Store<br/>(PostgreSQL)"]
    Cache["Cache<br/>(Redis)"]
    Serve["Serve<br/>(Router)"]
    
    Source --> Ingest
    Ingest --> Transform
    Transform --> Enrich
    Enrich --> Validate
    Validate --> Store
    Validate --> Cache
    Cache --> Serve
    Store --> Serve
    
    style Source fill:#bbdefb,stroke:#1976d2,stroke-width:2px
    style Serve fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
```

---

## 1️⃣2️⃣ Error Handling & Recovery Flow

```mermaid
graph TB
    Error["❌ Error Detected"]
    Log["📝 Log Event"]
    Guardian["🛡️ Guardian<br/>Classify"]
    Heal["💊 Healer<br/>Recover"]
    Retry["🔄 Retry"]
    Alert["🚨 Alert"]
    
    Error --> Log
    Log --> Guardian
    Guardian -->|Recoverable| Heal
    Guardian -->|Retry-able| Retry
    Guardian -->|Critical| Alert
    Heal -->|Success| Log
    Retry -->|Success| Log
    Alert -->|Manual| Log
    
    style Error fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style Heal fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Alert fill:#ffe0b2,stroke:#f57f17,stroke-width:2px
```

---

## 1️⃣3️⃣ Monitoring & Observability Stack

```mermaid
graph TB
    App["ADRION Services"]
    
    subgraph Observability["📊 Observability Stack"]
        Prometheus["Prometheus<br/>(Metrics)"]
        Grafana["Grafana<br/>(Dashboards)"]
        ELK["ELK Stack<br/>(Logs)"]
        Jaeger["Jaeger<br/>(Tracing)"]
    end
    
    subgraph Alerting["🚨 Alerting"]
        AlertMgr["AlertManager"]
        Slack["Slack"]
        PagerDuty["PagerDuty"]
    end
    
    App -->|Metrics| Prometheus
    App -->|Logs| ELK
    App -->|Traces| Jaeger
    
    Prometheus --> Grafana
    Prometheus --> AlertMgr
    ELK --> Grafana
    Jaeger --> Grafana
    
    AlertMgr --> Slack
    AlertMgr --> PagerDuty
    
    style App fill:#bbdefb,stroke:#1976d2,stroke-width:2px
    style Prometheus fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Grafana fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style AlertMgr fill:#ffe0b2,stroke:#f57f17,stroke-width:2px
```

---

*Wizualizacje zaktualizowane: 14.05.2026*

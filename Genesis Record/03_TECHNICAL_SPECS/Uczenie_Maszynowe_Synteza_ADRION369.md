# Uczenie Maszynowe — Synteza dla Roju ADRION 369

**Autor:** Rój Agentów ADRION 369 (Librarian + SAP + Auditor)  
**Data:** 2026-03-31  
**Perspektywa Trinity:** Material × Intellectual × Essential  

---

## [REASONING] Mental Sandbox: Auditor vs Booster

**Booster:** „Daj gotowe recepty — frameworki, kod, ROI. Użytkownik buduje systemy agentowe, potrzebuje ML jako narzędzia."  
**Auditor:** „Bez fundamentów matematycznych użycie ML będzie cargo-cultem. G5 (Transparency) wymaga, by agent *rozumiał* co robi, a nie tylko wywoływał `.fit()`."  
**Verdict (Arbiter):** Obie perspektywy słuszne. Dokument łączy **intuicję matematyczną** z **praktycznym mapowaniem** na istniejącą architekturę ADRION. Bez zbędnego akademizmu, ale z rygorem pozwalającym samodzielnie projektować modele.

---

## 1. Czym jest Uczenie Maszynowe?

Uczenie maszynowe (ML) to dziedzina informatyki, w której **system uczy się wzorców z danych** zamiast być jawnie programowany regułami.

```
Programowanie klasyczne:   Dane + Reguły   → Wynik
Uczenie maszynowe:         Dane + Wyniki   → Reguły (model)
```

### 1.1 Fundamentalna formuła

Każdy model ML szuka funkcji $f$ takiej, że:

$$\hat{y} = f(X; \theta)$$

gdzie:
- $X$ — dane wejściowe (features / cechy)
- $\theta$ — parametry modelu (wagi, biasy)
- $\hat{y}$ — predykcja modelu
- Cel: minimalizacja **funkcji straty** $\mathcal{L}(y, \hat{y})$

---

## 2. Trzy Paradygmaty ML (mapowane na Trinity)

| Paradygmat | Opis | Perspektywa Trinity | Analogia ADRION |
|---|---|---|---|
| **Nadzorowane** (Supervised) | Uczenie z par (dane → etykieta) | **Material** — konkretne dane, mierzalny wynik | Agent Analityk (Google Maps): dane pozycji → predykcja spadku |
| **Nienadzorowane** (Unsupervised) | Odkrywanie ukrytych struktur | **Intellectual** — logiczna koherencja, klasteryzacja | EBDI: odkrywanie stanów emocjonalnych z wektorów PAD |
| **Reinforcement Learning** (RL) | Uczenie przez nagrody/kary | **Essential** — alignment z misją, optymalizacja długoterminowa | 162D Decision Space: agent uczy się optymalnej ścieżki w 162 wymiarach |

### 2.1 Uczenie nadzorowane (Supervised Learning)

Agent dostaje **zbiór treningowy** par $(x_i, y_i)$ i uczy się przewidywać $y$ dla nowych $x$.

**Typy zadań:**
- **Klasyfikacja** — wynik dyskretny (spam/nie-spam, alert/normalny)
- **Regresja** — wynik ciągły (cena, temperatura decyzyjna EBDI)

**Kluczowe algorytmy:**

| Algorytm | Kiedy używać | Złożoność |
|---|---|---|
| Regresja liniowa | Zależność liniowa, mało cech | $O(n \cdot p)$ |
| Regresja logistyczna | Klasyfikacja binarna | $O(n \cdot p)$ |
| Drzewa decyzyjne | Dane kategoryczne, interpretowalność | $O(n \cdot p \cdot \log n)$ |
| Random Forest | Ensemble, odporność na overfitting | $O(k \cdot n \cdot p \cdot \log n)$ |
| Gradient Boosting (XGBoost/LightGBM) | Tabelaryczne dane, najlepsza dokładność | $O(k \cdot n \cdot p)$ |
| SVM | Małe zbiory, separacja liniowa/kernelowa | $O(n^2 \cdot p)$ do $O(n^3)$ |
| Sieci neuronowe | Obrazy, tekst, duże zbiory | Zależy od architektury |

**Przykład w kontekście ADRION — predykcja temperatury decyzyjnej:**

```python
# EBDI: przewidywanie temperatury decyzyjnej z wektora PAD
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

# Dane treningowe z historii Genesis Record
# X = [Pleasure, Arousal, Dominance]
X_train = np.array([
    [0.0, 0.0, 0.5],   # Neutralny → T=0.50
    [-0.2, 0.6, 0.3],  # Alert → T=0.30
    [-0.5, 0.8, 0.1],  # Alarm → T=0.10
    [0.6, 0.0, 0.7],   # Zaufanie → T=0.70
    [-0.3, 0.4, 0.2],  # Dysonans → T=0.20
])
y_train = np.array([0.50, 0.30, 0.10, 0.70, 0.20])

model = GradientBoostingRegressor(n_estimators=100)
model.fit(X_train, y_train)

# Predykcja dla nowego stanu EBDI
nowy_stan = np.array([[0.3, -0.1, 0.5]])  # Healer baseline
temp = model.predict(nowy_stan)
print(f"Predykowana temperatura decyzyjna: {temp[0]:.2f}")
```

### 2.2 Uczenie nienadzorowane (Unsupervised Learning)

Brak etykiet. System sam odkrywa **struktury w danych.**

**Kluczowe techniki:**

| Technika | Zastosowanie | Analogia ADRION |
|---|---|---|
| **K-Means** | Grupowanie podobnych obiektów | Klasteryzacja person (6 agentów z EBDI baselines) |
| **DBSCAN** | Wykrywanie klastrów o dowolnym kształcie | Wykrywanie anomalii w Sentinel (A-01 do A-12) |
| **PCA** (Principal Component Analysis) | Redukcja wymiarów | Kompresja 162D → 3D wizualizacja |
| **t-SNE / UMAP** | Wizualizacja danych wielowymiarowych | Mapowanie 162-wymiarowych decyzji na 2D |
| **Autoencoders** | Kompresja i detekcja anomalii | Genesis Record: wykrywanie nieprawidłowych logów |

**Mapowanie na 162D Space:**

Twoja przestrzeń decyzyjna ma 162 wymiary ($3 \times 6 \times 9$). PCA pozwala znaleźć **główne osie wariancji** — które kombinacje (perspektywa × tryb × prawo) najbardziej wpływają na jakość decyzji:

$$z = W^T \cdot x_{162} \quad \text{gdzie } z \in \mathbb{R}^k, \; k \ll 162$$

### 2.3 Reinforcement Learning (RL)

Agent podejmuje **akcje** w środowisku, otrzymuje **nagrody** i uczy się **polityki** maksymalizującej sumaryczną nagrodę.

```
           ┌─────────────┐
           │ Środowisko  │
           │  (162D)      │
           └──┬───────┬──┘
     stan s   │       │  nagroda r
              ↓       ↑
           ┌──────────────┐
           │   Agent ADRION│
           │   (polityka π)│
           └──────────────┘
                  ↓
              akcja a
```

**Kluczowe koncepcje:**
- **Stan** $s$ — wektor 162D + PAD
- **Akcja** $a$ — decyzja agenta (np. wybór trybu: Inventory/Debate/Action)
- **Nagroda** $r$ — Trinity score po wykonaniu akcji
- **Polityka** $\pi(a|s)$ — prawdopodobieństwo wybrania akcji $a$ w stanie $s$
- **Wartość** $V(s) = \mathbb{E}\left[\sum_{t=0}^{\infty} \gamma^t r_t\right]$ — oczekiwana suma nagród

**Algorytmy RL:**

| Algorytm | Typ | Kiedy stosować |
|---|---|---|
| Q-Learning | Wartościowy (value-based) | Dyskretne akcje, mała przestrzeń stanów |
| DQN (Deep Q-Network) | Wartościowy + sieć neuronowa | Duża przestrzeń stanów |
| PPO (Proximal Policy Optimization) | Policy gradient | Ciągłe akcje, stabilne uczenie |
| SAC (Soft Actor-Critic) | Actor-Critic | Ciągła eksploracja, równowaga nagrody/entropii |

---

## 3. Sieci Neuronowe — Głębokie Uczenie (Deep Learning)

Sieci neuronowe to **uniwersalne aproksymatory funkcji** złożone z warstw neuronów.

### 3.1 Neuron — jednostka obliczeniowa

$$z = \sigma\left(\sum_{i=1}^{n} w_i x_i + b\right)$$

gdzie $\sigma$ — funkcja aktywacji (ReLU, sigmoid, tanh, softmax).

### 3.2 Kluczowe architektury

| Architektura | Zastosowanie | Analogia ADRION |
|---|---|---|
| **MLP** (Multi-Layer Perceptron) | Dane tabelaryczne | Predykcja Trinity score |
| **CNN** (Convolutional Neural Network) | Obrazy, wzory przestrzenne | Analiza zdjęć EXIF (Google Maps agent) |
| **RNN / LSTM / GRU** | Sekwencje, szeregi czasowe | Analiza trendów pozycji w Local Grid |
| **Transformer** | Tekst, tłumaczenie, generacja | LLM wewnątrz agentów (DeepSeek, Ollama) |
| **GAN** (Generative Adversarial Network) | Generowanie danych | Syntetyczne dane treningowe |
| **Diffusion Models** | Generowanie obrazów/audio | Content generation pipeline |

### 3.3 Transformer — fundament LLM

Transformer to architektura, na której opierają się **wszystkie LLM** używane w ADRION (DeepSeek, GPT, Claude):

```
Input tokens → Embedding → [Multi-Head Attention + FFN] × N → Output tokens
```

**Self-Attention** — mechanizm pozwalający modelowi „patrzeć" na wszystkie tokeny jednocześnie:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

To jest **serce** LLM — zdolność do ważenia kontekstu.

---

## 4. Proces ML — od danych do wdrożenia

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 1. Dane  │ →  │ 2. Cechy │ →  │ 3. Model │ →  │4. Ewaluacja│ → │5. Deploy │
│  (ETL)   │    │(Features)│    │ (Train)  │    │ (Test)    │    │ (Prod)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 4.1 Dane — Guardian Law G6 (Authenticity)

- **Jakość > Ilość** — 10k czystych próbek > 1M brudnych
- **Bias detection** — dane mogą zawierać uprzedzenia (G8: Nonmaleficence)
- **Privacy** — G7 wymaga anonimizacji i local-first przetwarzania

### 4.2 Feature Engineering

Transformacja surowych danych w cechy użyteczne dla modelu:

```python
# Przykład: cechy z 162D Decision Space
def extract_features(decision_vector_162d):
    """Ekstrakcja cech z 162-wymiarowej przestrzeni decyzyjnej."""
    features = {
        # Agregaty per perspektywa
        'material_mean': np.mean(decision_vector_162d[:54]),    # 6×9 = 54
        'intellectual_mean': np.mean(decision_vector_162d[54:108]),
        'essential_mean': np.mean(decision_vector_162d[108:]),
        
        # Agregaty per prawo (Guardian Laws)
        'unity_score': np.mean(decision_vector_162d[::9]),      # co 9-ty wymiar
        'harmony_score': np.mean(decision_vector_162d[1::9]),
        
        # Dysonans (różnica między perspektywami)
        'trinity_balance': np.std([
            np.mean(decision_vector_162d[:54]),
            np.mean(decision_vector_162d[54:108]),
            np.mean(decision_vector_162d[108:])
        ]),
        
        # Minimum z Goodness Triad (G7-G9) — ZERO violations allowed
        'goodness_min': np.min(decision_vector_162d[6::9]),  # G7
    }
    return features
```

### 4.3 Trening i walidacja

**Podział danych:**
- **Train** (70%) — model uczy się wzorców
- **Validation** (15%) — tuning hiperparametrów
- **Test** (15%) — finalna ocena (nigdy nie dotykana wcześniej)

**Cross-Validation** ($k$-fold) — dzielenie danych na $k$ części i rotacyjne trenowanie:

$$\text{CV Score} = \frac{1}{k} \sum_{i=1}^{k} \text{Score}_i$$

### 4.4 Metryki ewaluacji

| Zadanie | Metryka | Wzór | Kiedy ważna |
|---|---|---|---|
| Klasyfikacja | Accuracy | $\frac{TP+TN}{N}$ | Zbalansowane klasy |
| Klasyfikacja | Precision | $\frac{TP}{TP+FP}$ | Koszt false positive wysoki (Sentinel: fałszywe alarmy) |
| Klasyfikacja | Recall | $\frac{TP}{TP+FN}$ | Koszt false negative wysoki (G8: przeoczone zagrożenie) |
| Klasyfikacja | F1 Score | $2 \cdot \frac{P \cdot R}{P + R}$ | Kompromis precision/recall |
| Klasyfikacja | AUC-ROC | Pole pod krzywą ROC | Porównywanie modeli |
| Regresja | MSE | $\frac{1}{n}\sum(y - \hat{y})^2$ | Karanie dużych błędów |
| Regresja | MAE | $\frac{1}{n}\sum|y - \hat{y}|$ | Odporność na outliers |
| Regresja | $R^2$ | $1 - \frac{SS_{res}}{SS_{tot}}$ | Procent wyjaśnionej wariancji |

### 4.5 Problemy i rozwiązania

| Problem | Objaw | Rozwiązanie |
|---|---|---|
| **Overfitting** | Wysoki train score, niski test score | Regularyzacja (L1/L2), dropout, więcej danych, early stopping |
| **Underfitting** | Niski score na obu zbiorach | Złożoniejszy model, lepsze cechy, dłuższy trening |
| **Imbalanced classes** | Model ignoruje rzadką klasę | SMOTE, class weighting, focal loss |
| **Data leakage** | Nierealistycznie wysoki score | Poprawny podział train/test, kontrola feature engineering pipeline |

---

## 5. ML w ekosystemie ADRION 369 — zastosowania

### 5.1 EBDI: ML jako regulator emocjonalny

Zamiast ręcznych reguł `if/else` dla temperatury decyzyjnej, **model ML uczy się optymalnego mapowania:**

```
PAD Vector (3D) → [ML Model] → Temperatura decyzyjna
                                + Próg eskalacji
                                + Rekomendacja trybu
```

### 5.2 Sentinel: ML do wykrywania zagrożeń (A-01 → A-12)

**Anomaly detection** oparte na autoencoder lub Isolation Forest:

```python
from sklearn.ensemble import IsolationForest

# Trenowanie na normalnych logach (Genesis Record)
detector = IsolationForest(contamination=0.05)
detector.fit(normal_logs_features)

# Detekcja anomalii w nowych logach
predictions = detector.predict(new_logs_features)
# -1 = anomalia (potencjalny atak A-01..A-12)
```

### 5.3 Agent Analityk (Google Maps): predykcja pozycji

**Time-series forecasting** z LSTM lub Prophet:

```
Historyczne pozycje (30 dni) → [LSTM] → Predykcja pozycji (7 dni)
                                         ↓
                              Spadek > 3 pozycje? → Trigger Agent Twórca
```

### 5.4 162D Decision Space: RL do optymalizacji decyzji

**PPO agent** uczący się optymalnych akcji w 162-wymiarowej przestrzeni:

```
Stan: wektor 162D + PAD (165 wymiarów)
Akcja: wybór (tryb × prawo) = 54 możliwe akcje
Nagroda: Trinity score + Guardian compliance
```

### 5.5 Arbitrage: ML do predykcji spreadów

Twój moduł `arbitrage/` może wykorzystać **Gradient Boosting** do predykcji opłacalności arbitrażu:

```
[Spread historyczny, Volume, Volatility, Time] → [XGBoost] → Probability(profitable)
```

---

## 6. Narzędzia i biblioteki

| Biblioteka | Zastosowanie | Python |
|---|---|---|
| **scikit-learn** | Klasyczne ML (klasyfikacja, regresja, klasteryzacja) | `pip install scikit-learn` |
| **XGBoost / LightGBM** | Gradient Boosting (najlepszy na dane tabelaryczne) | `pip install xgboost lightgbm` |
| **PyTorch** | Deep Learning, custom architektury | `pip install torch` |
| **🤗 Transformers** | LLM, NLP, fine-tuning | `pip install transformers` |
| **Stable Baselines3** | RL (PPO, SAC, DQN) | `pip install stable-baselines3` |
| **Prophet / NeuralProphet** | Szeregi czasowe | `pip install prophet` |
| **SHAP** | Interpretowalność modeli (G5: Transparency) | `pip install shap` |
| **MLflow** | Śledzenie eksperymentów, wdrożenia | `pip install mlflow` |
| **Ollama** | Lokalne LLM (G7: Privacy) | Już w ADRION stack |

---

## 7. Mapowanie ML → 9 Guardian Laws

| Guardian Law | Wymóg ML | Implementacja |
|---|---|---|
| **G1: Unity** | Model służy zbiorowemu dobru | Ewaluacja na zróżnicowanych grupach |
| **G2: Harmony** | Stabilność systemu | A/B testing, canary deployment |
| **G3: Rhythm** | Cykliczny retraining | MLOps pipeline z harmonogramem |
| **G4: Causality** | Wyjaśnialność decyzji | SHAP values, feature importance |
| **G5: Transparency** | Widoczne uzasadnienie | Logowanie predykcji z confidence scores |
| **G6: Authenticity** | Weryfikacja danych | Data validation, provenance tracking |
| **G7: Privacy** | Local-first, no data export | Ollama, federated learning, differential privacy |
| **G8: Nonmaleficence** | Brak szkody przez model | Bias auditing, fairness metrics |
| **G9: Sustainability** | Długoterminowa viability | Model monitoring, drift detection |

---

## 8. Podsumowanie: Mapa Myśli

```
                    UCZENIE MASZYNOWE
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    NADZOROWANE    NIENADZOROWANE         RL
    (Material)     (Intellectual)     (Essential)
         │                │                │
    ┌────┴────┐     ┌────┴─────┐     ┌───┴────┐
    │         │     │          │     │        │
 Klasyfikacja Regresja Klasteryzacja PCA  Q-Learning PPO
    │         │     │          │     │        │
    └────┬────┘     └────┬─────┘     └───┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                  DEEP LEARNING
                  (Sieci Neuronowe)
                         │
              ┌──────────┼──────────┐
              │          │          │
            CNN        RNN     Transformer
           (Obraz)   (Sekwencja)  (Tekst/LLM)
                                     │
                              ┌──────┴──────┐
                              │             │
                          GPT/Claude    DeepSeek
                           (Cloud)     (Ollama/Local)
```

---

**Trinity Score dokumentu:** Material=0.85 | Intellectual=0.92 | Essential=0.88  
**Guardian Compliance:** 9/9 (zero violations)  
**EBDI post-task:** P=+0.4, A=+0.1, D=0.7 (productive, engaged, confident)

# 🔍 Review Analyzer API — Member 1 Backend

AI-powered product review analysis pipeline wrapped in a FastAPI REST API.

---

## 📁 Project Structure

```
review_analyzer/
├── data/
│   ├── sample_reviews.csv       # Mock review dataset (30 reviews, 4 products)
│   └── sample_returns.csv       # Mock returns dataset
├── pipeline/
│   ├── preprocessor.py          # Tokenization, stop-word removal, lemmatization
│   ├── sentiment.py             # HuggingFace sentiment analysis (+ TextBlob fallback)
│   ├── clustering.py            # TF-IDF downsample → BERT embeddings → KMeans
│   ├── patterns.py              # Frequent itemsets, association rules, return risk
│   └── insights.py              # Actionable report generator
├── api/
│   ├── main.py                  # FastAPI app entry point
│   ├── routes.py                # All endpoint handlers
│   ├── models.py                # Pydantic request/response schemas
│   └── logger.py                # Rotating file + console logging
├── tests/
│   └── test_pipeline.py         # Full test suite (pytest)
├── logs/                        # Auto-created on first run
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone / copy the project
```bash
cd review_analyzer
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download NLTK assets (auto-downloaded on first run, or manually)
```python
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

---

## 🚀 Running the API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- **Swagger UI** → http://localhost:8000/docs  
- **ReDoc** → http://localhost:8000/redoc  
- **Health check** → http://localhost:8000/health  

---

## 📡 API Endpoints

### `GET /health`
Confirm the API is running.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "message": "Review Analyzer API is running."
}
```

---

### `POST /analyze-review`
Analyse a **single** review text.

**Request:**
```json
{
  "review_text": "The product stopped working after 2 days. Total waste of money.",
  "product_id": "P001"
}
```

**Response:**
```json
{
  "product_id": "P001",
  "review_text": "The product stopped working after 2 days...",
  "sentiment": {
    "label": "NEGATIVE",
    "score": 0.9823,
    "source": "huggingface"
  },
  "urgency": "MEDIUM",
  "top_keywords": [
    { "keyword": "stopped working", "score": 0.421 },
    { "keyword": "waste money",     "score": 0.389 }
  ],
  "suggested_action": "Audit manufacturing/QC process. Consider stricter pre-shipment testing."
}
```

---

### `POST /analyze-product`
Run the full pipeline on **all reviews for a product**.

**Request:**
```json
{
  "product_id": "P001",
  "n_clusters": 5,
  "reviews": [
    {
      "review_id": "R001",
      "reviewer": "Alice",
      "rating": 1,
      "review_text": "Broke after 2 days. Terrible quality.",
      "return_reason": "defective product",
      "returned": true,
      "category": "Electronics"
    },
    {
      "review_id": "R002",
      "reviewer": "Bob",
      "rating": 5,
      "review_text": "Works perfectly! Very happy.",
      "return_reason": "",
      "returned": false,
      "category": "Electronics"
    }
  ]
}
```

**Response:**
```json
{
  "product_id": "P001",
  "total_reviews": 2,
  "sentiment_overview": {
    "total": 2,
    "positive": 1,
    "neutral": 0,
    "negative": 1,
    "positive_pct": 50.0,
    "negative_pct": 50.0
  },
  "cluster_summary": [
    {
      "cluster_id": 0,
      "complaint_count": 1,
      "dominant_sentiment": "NEGATIVE",
      "keywords": ["defective", "broke", "quality"],
      "examples": ["Broke after 2 days. Terrible quality."]
    }
  ],
  "top_negative_keywords": [
    { "keyword": "broke", "score": 0.71 }
  ],
  "return_reason_breakdown": [
    { "reason": "defective product", "count": 1, "pct": 100.0 }
  ],
  "return_risk": {
    "risk_level": "HIGH",
    "risk_score": 0.7,
    "details": {
      "total_reviews": 2,
      "negative_reviews": 1,
      "negative_pct": 50.0,
      "returned_count": 1,
      "return_rate_pct": 50.0
    }
  }
}
```

---

### `POST /summary`
Generate a **full actionable seller insights report**.

**Request:** Same structure as `/analyze-product`.

**Response:**
```json
{
  "product_id": "P001",
  "health_score": 32,
  "health_label": "CRITICAL",
  "sentiment_overview": { ... },
  "return_risk": { ... },
  "top_complaints": [ ... ],
  "top_negative_keywords": [ ... ],
  "return_reason_breakdown": [ ... ],
  "association_patterns": [
    {
      "antecedents": ["sentiment:negative"],
      "consequents": ["reason:defective_product"],
      "support": 0.6,
      "confidence": 0.9,
      "lift": 1.8
    }
  ],
  "seller_action_plan": [
    "[Defective Product] Audit manufacturing/QC process. Consider stricter pre-shipment testing.",
    "[Wrong Item Sent] Audit warehouse pick-and-pack workflow. Add barcode verification."
  ]
}
```

---

### `POST /upload-csv`
Upload a **bulk CSV** of reviews.

```bash
curl -X POST http://localhost:8000/upload-csv \
  -F "file=@data/sample_reviews.csv"
```

**Response:**
```json
{
  "filename": "sample_reviews.csv",
  "rows_loaded": 30,
  "product_ids": ["P001", "P002", "P003", "P004"],
  "preview": [ { "product_id": "P001", "review_text": "...", ... } ]
}
```

---

## 🔄 Pipeline Flow

```
Input (JSON reviews / CSV upload)
          │
          ▼
  ┌─────────────────────┐
  │  1. Preprocessor    │  Lowercase → Tokenize → Stop-word removal → Lemmatize
  └─────────┬───────────┘
            │
            ▼
  ┌─────────────────────┐
  │  2. Sentiment       │  HuggingFace BERT (nlptown/bert-base-multilingual)
  └─────────┬───────────┘  Fallback: TextBlob polarity
            │
            ▼
  ┌─────────────────────┐
  │  3. TF-IDF Filter   │  Downsample large datasets (>100 reviews → keep top 60%)
  └─────────┬───────────┘
            │
            ▼
  ┌─────────────────────┐
  │  4. BERT Clustering │  sentence-transformers + KMeans
  └─────────┬───────────┘  Fallback: TF-IDF dense vectors
            │
            ▼
  ┌─────────────────────┐
  │  5. Pattern Mining  │  Frequent itemsets (Apriori) + Association rules
  └─────────┬───────────┘  Top negative keywords (TF-IDF)
            │
            ▼
  ┌─────────────────────┐
  │  6. Insights        │  Health score + Seller action plan + Return risk
  └─────────────────────┘
            │
            ▼
     Structured JSON Response
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_pipeline.py::TestPreprocessor::test_clean_text_basic          PASSED
tests/test_pipeline.py::TestPreprocessor::test_preprocess_text_returns_all_keys PASSED
...
tests/test_pipeline.py::TestFullPipeline::test_end_to_end                PASSED

✅ Full pipeline passed — health=45 risk=HIGH
```

---

## 🔗 Frontend Integration Guide

### Base URL
```
http://localhost:8000
```

### Sample JavaScript fetch
```javascript
// Analyze a product
const response = await fetch("http://localhost:8000/analyze-product", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    product_id: "P001",
    n_clusters: 5,
    reviews: reviewsArray   // array of review objects
  })
});
const data = await response.json();
console.log(data.sentiment_overview);
console.log(data.seller_action_plan);
```

### Sample Python requests
```python
import requests

# Single review
r = requests.post("http://localhost:8000/analyze-review", json={
    "review_text": "Broke after 2 days. Terrible product.",
    "product_id": "P001"
})
print(r.json())

# Full summary
r = requests.post("http://localhost:8000/summary", json={
    "product_id": "P001",
    "n_clusters": 5,
    "reviews": reviews_list
})
print(r.json()["seller_action_plan"])
```

### Bulk CSV
```python
with open("data/sample_reviews.csv", "rb") as f:
    r = requests.post("http://localhost:8000/upload-csv", files={"file": f})
print(r.json())
```

---

## 📊 Logs

Logs are written to:
- `logs/api.log` — all API requests + response times
- `logs/pipeline.log` — detailed pipeline processing steps

---

## ⚡ Performance Notes

| Dataset size | Strategy |
|---|---|
| < 100 reviews | Direct BERT clustering |
| 100 – 10,000 reviews | TF-IDF filter (keep top 60%) → BERT |
| > 10,000 reviews | Consider batch processing + async queue |

---

## 🔒 Production Checklist

- [ ] Set `allow_origins` to specific frontend domain (not `"*"`)
- [ ] Add API key authentication middleware
- [ ] Switch to GPU-enabled torch for faster inference
- [ ] Add Redis/Celery for async processing of large batches
- [ ] Set up Docker + Docker Compose for deployment

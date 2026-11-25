# Coffee Rating Application

A full-stack, responsive web application for exploring artisan coffees and casting live votes for your favourite brews.

The application has been developed in three modular phases:
- **Module 1**: Frontend development with modern semantic HTML5, CSS3 coffee-inspired design, and Vanilla JavaScript.
- **Module 2**: High-performance backend API built with FastAPI, Pydantic data validation, and Swagger documentation.
- **Module 3**: Database integration with SQLite, SQLAlchemy ORM, atomic voting transactions, and complete frontend-to-backend API integration.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Grid, Flexbox, Custom Variables), Vanilla JavaScript (ES6+), Zero External Frameworks |
| **Backend** | Python 3, FastAPI, Pydantic v2, Uvicorn (ASGI) |
| **Database** | SQLite 3, SQLAlchemy 2.0 ORM, Atomic Transactions |

---

## 📁 Project Structure

```text
Coffee-Rating-Application/
├── frontend/
│   ├── index.html        # Semantic HTML5 markup, accessible landmarks & cards container
│   ├── style.css         # Warm coffee palette, responsive grid, card styles, loading & toast states
│   └── script.js         # API integration: live data fetching, voting, duplicate prevention & toasts
├── backend/
│   ├── main.py           # FastAPI application, lifespan DB init, CORS & API endpoints
│   ├── models.py         # Pydantic schemas (CoffeeResponse, HealthResponse, ErrorResponse)
│   ├── database.py       # SQLAlchemy engine, SessionLocal factory, Coffee ORM model & seed logic
│   ├── requirements.txt  # Python package specifications (fastapi, uvicorn, pydantic, sqlalchemy)
│   ├── coffee_rating.db  # SQLite database storing persistent coffees and vote counts
│   └── test_backend.py   # 12-point automated verification suite against isolated test DB
└── README.md             # Comprehensive project documentation
```

---

## 🗄️ Database Schema & Storage

The SQLite database is located at:
`backend/coffee_rating.db`

### Table: `coffees`

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | String | Primary Key, Indexed | Unique slug identifier (e.g. `cappuccino`, `espresso`) |
| `name` | String | Not Null | Display name of the coffee |
| `description`| String | Not Null | Flavor profile description |
| `image_url` | String | Not Null | High-definition coffee image URL |
| `votes` | Integer| Default 0, Not Null | Persistent vote count |

### Database Features:
- **Auto-Initialization**: Tables and initial coffee records are created automatically on backend startup.
- **Vote Preservation**: Existing vote counts are retained across server restarts and are never reset.
- **Duplicate Prevention**: Only inserts initial records if their IDs are not already in the database.
- **Atomic Transactions**: Votes are incremented with atomic SQL statements (`UPDATE coffees SET votes = votes + 1 WHERE id = :id`) to guarantee zero lost votes during high concurrency.

---

## ☕ Coffee Catalogue Data

| ID | Name | Description | Default Votes |
| :--- | :--- | :--- | :---: |
| `cappuccino` | **Cappuccino** | A harmonious balance of rich espresso, velvety steamed milk, and a luxurious cloud of foam. | 0 |
| `iced-latte` | **Iced Latte** | Chilled espresso poured gently over crisp iced milk for a refreshing, silky-smooth coffee experience. | 0 |
| `espresso` | **Espresso** | An intense, concentrated shot crowned with a dense, hazelnut-toned golden crema. | 0 |
| `cold-brew` | **Cold Brew** | Slow-steeped in cold water for 18 hours to unlock ultra-smooth, naturally sweet, low-acid notes. | 0 |

---

## 🔌 API Endpoints

All endpoints support Cross-Origin Resource Sharing (CORS) for local frontend interaction.

| Method | Endpoint | Description | Response Model | Status |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/health` | Backend operational check | `HealthResponse` | `200 OK` |
| `GET` | `/api/coffees` | Returns all coffees with current SQLite vote counts | `List[CoffeeResponse]` | `200 OK` |
| `POST` | `/api/coffees/{coffee_id}/vote` | Atomically increments vote count by 1 | `CoffeeResponse` | `200 OK` |
| `POST` | `/api/coffees/{coffee_id}/vote` | Returns 404 if coffee ID is invalid | `ErrorResponse` | `404 Not Found` |
| `GET` | `/docs` | Interactive Swagger UI API documentation | HTML | `200 OK` |
| `GET` | `/redoc` | Interactive ReDoc API documentation | HTML | `200 OK` |

---

## 🚀 How to Run the Application

### 1. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the FastAPI Backend
```bash
# From within the backend directory:
uvicorn main:app --reload --port 8000

# Or using Python:
python -m uvicorn main:app --reload --port 8000
```
- API will be accessible at: `http://127.0.0.1:8000`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

### 3. Open the Frontend
Simply double-click `frontend/index.html` or open it in any web browser. It automatically detects the running backend at `http://127.0.0.1:8000`, loads live database vote counts, and submits live votes.

---

## 🧪 Automated Testing

An automated verification test suite runs against an isolated, temporary SQLite test database (`test_coffee_rating.db`) so real data is never disturbed:

```bash
python backend/test_backend.py
```

### Verified Test Criteria:
1. [x] Database is created automatically on startup.
2. [x] All four coffee records are populated in SQLite.
3. [x] Initial vote counts are zero in a fresh database.
4. [x] `GET /api/coffees` retrieves records directly from SQLite.
5. [x] Voting increases the targeted coffee count by exactly one.
6. [x] Voting twice increases the count by two.
7. [x] Voting for one coffee does not alter other coffee counts.
8. [x] Invalid coffee ID returns `HTTP 404`.
9. [x] Existing vote counts remain unchanged across backend restarts.
10. [x] Concurrent voting requests do not lose increments (atomic transactions verified).
11. [x] Frontend dynamically fetches and renders database vote counts on page load.
12. [x] Frontend disables buttons during in-flight requests to prevent duplicate clicks and updates DOM with backend response.

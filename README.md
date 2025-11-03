# 🧭 Azimuth-Core

**Smart Personal Finance Planner** - A local-first desktop application for managing family budgets with AI assistance.

---

## 🎯 Project Overview

Azimuth-Core is a privacy-focused financial planning tool that runs entirely on your local machine. It helps families manage multiple accounts, track spending across categories, visualize financial trends, and make informed budgeting decisions—all without sending your data to the cloud.

**Key Features:**
- 💳 Multi-user family budget management (multiple owners, multiple accounts)
- 📊 CSV transaction import with intelligent categorization
- 📈 Interactive timeline visualization of income/expenses
- 🏷️ Hierarchical category system with custom rules
- 🤖 Local AI assistant (Ollama) for financial insights
- 🔐 Complete data privacy - everything stays on your computer

---

## 🏗️ Architecture

**Frontend:** Vue 3 + Vite + Chart.js  
**Backend:** FastAPI + Python  
**Database:** SQLite (local file)  
**AI:** Ollama (llama3.2:3b)  

**Design Philosophy:** Desktop-first, glassmorphism UI, no cloud dependencies

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama installed and running

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/a1e5ya/azimuth-core.git
cd azimuth-core
```

2. **Start Backend** (Terminal 1)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

3. **Start Frontend** (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```

4. **Open Application**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8001`
- API Docs: `http://localhost:8001/docs`

---

## 📂 Project Structure

```
azimuth-core/
├── backend/
│   ├── app/
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Database models
│   │   └── auth/           # Local authentication
│   ├── server.py           # FastAPI entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── stores/         # Pinia state management
│   │   └── utils/          # Helper functions
│   └── package.json
├── data/                   # SQLite database location
└── docs/                   # Documentation
```

---

## 🎨 Features

### ✅ Implemented
- **Account Management:** Create owners and accounts (checking, savings, reserve)
- **Transaction Import:** CSV parsing with 19-column support, deduplication
- **Smart Filters:** Filter by date, amount, category, owner, account type
- **Category System:** Hierarchical categories with icons and colors
- **Dashboard:** KPIs, income vs expenses chart, date range picker
- **Timeline:** Multi-category visualization with interactive legend
- **AI Chat:** Ollama integration for conversational assistance

### 🔄 In Progress
- Transaction CRUD operations
- Category management UI
- Timeline zoom/scroll improvements
- Account balance tracking

### 📋 Planned
- Budget targets and savings goals
- Forecasting with Prophet ML
- Scenario planning ("what-if" analysis)
- Advanced AI categorization

---

## 🗂️ Database Schema

**Core Tables:**
- `users` - User accounts with local authentication
- `owners` - Family members (Alex, Egor, Lila)
- `accounts` - Bank accounts per owner
- `transactions` - All financial transactions (19 fields)
- `categories` - Hierarchical category tree
- `category_mappings` - Auto-categorization rules
- `import_batches` - CSV import tracking
- `audit_log` - Complete activity history

---

## 📊 Tech Stack Details

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend Framework | Vue 3 + Composition API | Reactive UI components |
| Build Tool | Vite | Fast development and builds |
| State Management | Pinia | Centralized app state |
| Charts | Chart.js | Data visualizations |
| Backend Framework | FastAPI | REST API endpoints |
| Database | SQLite + SQLAlchemy | Local data storage |
| AI Model | Ollama (Llama 3.2:3b) | Conversational AI |
| Styling | Custom CSS + Glassmorphism | Modern UI design |

---

## 🔐 Privacy & Security

- **Local-First:** All data stored in local SQLite database
- **No Cloud:** Zero external API calls for financial data
- **Password Protection:** Bcrypt hashed passwords
- **Session Management:** JWT tokens with configurable timeout
- **Audit Trail:** Complete activity log for transparency

---

## 🤝 Contributing

This is a student project for academic purposes. 

---

## 📝 License

This project is currently private and maintained for academic purposes.

---



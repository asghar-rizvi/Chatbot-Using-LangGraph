# AI Chatbot — Tools, RAG & Streaming

A full-stack AI chatbot built with **FastAPI**, **LangGraph**, and **Gemini**, featuring real-time streaming, multi-tool calling with live indicators, PDF-based RAG, multi-chat support, and a dark-themed UI.

<br>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-Agent_Framework-blue" />
  <img src="https://img.shields.io/badge/Gemini_2.0-Flash-orange?logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/FAISS-Vector_Store-yellow" />
</p>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔁 **Real-time Streaming** | Token-by-token response via SSE (`astream_events` → frontend `ReadableStream`) |
| 🛠️ **Multi-Tool Calling** | Calculator, Stock Prices, Web Search, Document Search — all with live UI indicators |
| 📄 **PDF RAG** | Upload PDFs from the UI → chunked, embedded, stored in FAISS → searchable by the agent |
| 💬 **Multi-Chat Support** | Create, switch, delete chats — each with a unique ID generated on the frontend |
| 💾 **Persistent History** | All messages saved in SQLite, reloaded on chat select |
| 🎨 **Dark Theme UI** | GitHub-dark inspired, responsive design with HTML/CSS/JS — no frameworks |
| ⚡ **Tool Indicators** | Animated spinners show which tool is being called, with a checkmark on completion |
| 📱 **Responsive** | Collapsible sidebar, works on mobile and desktop |

---

## 🛠️ Tools

The agent has access to the following tools and autonomously decides when to use them:

```
🧮 Calculator
├── add(a, b)
├── subtract(a, b)
├── multiply(a, b)
└── divide(a, b)

📈 Stock Price
└── get_stock_price(symbol)     → real-time via alphavantage

🔍 Web Search
└── web_search(query)           → DuckDuckGo

📄 Document Search (RAG)
└── search_documents(query)     → FAISS similarity search over uploaded PDFs
```

---

## 🏗️ Architecture

```
User (Browser)
  │
  │  HTTP / SSE
  ▼
┌──────────────────────────────────┐
│           FastAPI Server         │
│                                  │
│  routes/chat.py    routes/upload │
│       │                  │       │
│       ▼                  ▼       │
│  services/agent    services/rag  │
│       │                  │       │
│   LangGraph          FAISS +     │
│   Agent Loop         Embeddings  │
│       │                          │
│   services/tools                 │
│   ┌──────────┐                   │
│   │ add      │                   │
│   │ subtract │                   │
│   │ multiply │                   │
│   │ divide   │                   │
│   │ stocks   │                   │
│   │ search   │                   │
│   │ RAG      │                   │
│   └──────────┘                   │
│                                  │
│         database.py (SQLite)     │
└──────────────────────────────────┘
```

---

## 📂 Project Structure

```
chatbot_project/
│
├── main.py                  # FastAPI app, lifespan, static mount
├── database.py              # SQLite async operations (aiosqlite)
├── .env                     # GOOGLE_API_KEY
├── requirements.txt
│
├── routes/
│   ├── chat.py              # Chat CRUD + SSE streaming endpoint
│   └── upload.py            # PDF upload endpoint
│
├── services/
│   ├── agent.py             # LangGraph agent, graph builder, stream_response
│   ├── tools.py             # All tool definitions
│   └── rag.py               # PDF loading, FAISS vector store, search
│
├── static/
│   ├── index.html           # Single page UI
│   ├── style.css            # Dark theme styles
│   └── script.js            # Chat logic, SSE parsing, tool indicators
│
└── uploads/                 # Uploaded PDFs stored here
```

---

## 🔄 How Streaming Works

```
 Backend                              Frontend
────────                             ─────────

astream_events()
    │
    ├─ on_tool_start ──────────►  Show spinner pill
    │                              "📈 Fetching stock price…"
    │
    ├─ on_tool_end ────────────►  Show checkmark pill
    │                              "✓ Fetching stock price done"
    │
    ├─ on_chat_model_stream ───►  Append token to bubble
    │   (token by token)           Render markdown live
    │
    └─ end ────────────────────►  Save full response to DB
```

**SSE event format:**

```json
{"type": "tool_start", "name": "get_stock_price"}
{"type": "tool_end",   "name": "get_stock_price"}
{"type": "token",      "content": "The current"}
{"type": "token",      "content": " price of"}
{"type": "end",        "full_response": "The current price of..."}
```

---

## 💬 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chats` | Create a new chat `{id, title}` |
| `GET` | `/api/chats` | List all chats |
| `DELETE` | `/api/chats/:id` | Delete a chat and its messages |
| `GET` | `/api/chats/:id/messages` | Get message history for a chat |
| `POST` | `/api/chats/:id/message` | Send message, returns SSE stream |
| `POST` | `/api/upload` | Upload a PDF for RAG |

---

## 🧩 Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini 2.0 Flash |
| **Agent Framework** | LangGraph (StateGraph + ToolNode) |
| **Backend** | FastAPI + Uvicorn |
| **Database** | SQLite via aiosqlite |
| **Vector Store** | FAISS + Google Embeddings |
| **PDF Parsing** | pypdf |
| **Stock Data** | yfinance |
| **Web Search** | DuckDuckGo (langchain-community) |
| **Frontend** | Vanilla HTML / CSS / JS |
| **Streaming** | Server-Sent Events (SSE) |

---

## 📸 UI Preview

```
┌──────────────────┬──────────────────────────────────────────────┐
│  🤖 Chats        │                                              │
│  [+ New]         │  You: What's the price of TSLA?              │
│                  │                                              │
│  ● TSLA Price    │  🤖: ┌──────────────────────────────┐        │
│  ● PDF Question  │      │ 📈 Fetching stock price…     │        │
│  ● Calculator    │      │ ✓  Fetching stock price done │        │
│                  │      └──────────────────────────────┘        │
│                  │                                              │
│                  │      Tesla (TSLA) is currently trading       │
│                  │      at **$248.30**                          │
│                  │      Open: $245.10 | High: $250.80           │
│                  │      Low: $244.50                            │
│                  │                                              │
│                  │                                              │
│ 📄 Upload PDF    │  [Type a message…                ] [➤ Send] │
│ ✅ doc.pdf — 24  │                                              │
└──────────────────┴──────────────────────────────────────────────┘
```


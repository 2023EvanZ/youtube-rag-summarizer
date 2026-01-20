# 📺 YouTube RAG Notetaker

AI-powered YouTube transcript summarization using RAG (Retrieval Augmented Generation) with Gemini and ChromaDB.

## ✨ Features

- 🎥 **YouTube Transcript Extraction**: Automatically fetch and process video transcripts
- 🤖 **AI-Powered Summarization**: Generate concise, easy-to-understand notes using Google Gemini
- 🔍 **RAG Context**: Semantic search using ChromaDB for better note generation
- 👤 **User Authentication**: Secure login system with Supabase PostgreSQL
- 📊 **Admin Dashboard**: Manage users and view usage metrics
- 🎨 **Clean UI**: Built with Streamlit for a modern, responsive interface

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│            Streamlit Frontend               │
├─────────────────────────────────────────────┤
│                                             │
│  User Auth ──────────► Supabase            │
│                        PostgreSQL           │
│                                             │
│  Note Generation ────► ChromaDB             │
│                        Vector Store         │
│                                             │
│  LLM Processing ─────► Google Gemini        │
│                        API                  │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key
- Supabase account (free tier)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/youtube-rag-notetaker.git
   cd youtube-rag-notetaker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv backend/.venv
   source backend/.venv/bin/activate  # On Windows: backend\.venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example backend/.env
   # Edit backend/.env with your credentials
   ```

5. **Set up Supabase database**
   - Create a free account at [supabase.com](https://supabase.com)
   - Create a new project
   - Go to SQL Editor and run:
   
   ```sql
   -- Users table
   CREATE TABLE IF NOT EXISTS users (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       username TEXT UNIQUE NOT NULL,
       email TEXT UNIQUE NOT NULL,
       hashed_password TEXT NOT NULL,
       is_admin BOOLEAN DEFAULT FALSE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       last_login TIMESTAMP WITH TIME ZONE,
       CONSTRAINT username_length CHECK (char_length(username) >= 3),
       CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
   );
   
   CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
   CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
   
   -- Metrics table
   CREATE TABLE IF NOT EXISTS metrics (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       username TEXT NOT NULL,
       action TEXT NOT NULL,
       timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       video_id TEXT,
       duration REAL,
       error TEXT,
       context TEXT
   );
   
   CREATE INDEX IF NOT EXISTS idx_metrics_username ON metrics(username);
   CREATE INDEX IF NOT EXISTS idx_metrics_action ON metrics(action);
   CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC);
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Login with default admin**
   - Username: (from your .env `DEFAULT_ADMIN_USERNAME`)
   - Password: (from your .env `DEFAULT_ADMIN_PASSWORD`)
   - ⚠️ **Change the password immediately after first login!**

## 📝 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | ✅ Yes |
| `SUPABASE_URL` | Your Supabase project URL | ✅ Yes |
| `SUPABASE_KEY` | Supabase anonymous key | ✅ Yes |
| `DEFAULT_ADMIN_USERNAME` | Default admin username | ✅ Yes |
| `DEFAULT_ADMIN_PASSWORD` | Default admin password | ✅ Yes |
| `DEFAULT_ADMIN_EMAIL` | Default admin email | ✅ Yes |
| `CHROMA_PATH` | ChromaDB storage path | ❌ Optional |

### Getting API Keys

1. **Google Gemini API**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Copy to `.env`

2. **Supabase**
   - Sign up at [supabase.com](https://supabase.com)
   - Create a project
   - Go to Settings → API
   - Copy `URL` and `anon/public` key

## 🎯 Usage

1. **Login**: Use your credentials or create a new account
2. **Paste YouTube URL**: Enter any YouTube video URL
3. **Generate Notes**: Click "Generate Transcript + Notes"
4. **Download**: Save notes as Markdown file

### Admin Features

- 📊 View usage metrics and analytics
- 👥 Manage user accounts
- 🔑 Promote/demote admin privileges
- 🗑️ Delete user accounts

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.11
- **LLM**: Google Gemini 2.5 Flash
- **Vector DB**: ChromaDB
- **User DB**: Supabase (PostgreSQL)
- **Auth**: Argon2 password hashing
- **Video API**: YouTube Transcript API

## 📦 Project Structure

```
youtube-rag-notetaker/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── backend/
│   ├── auth.py           # Authentication logic
│   ├── supabase_db.py    # Supabase database operations
│   ├── notes_db.py       # ChromaDB operations
│   ├── gen_transcript.py # YouTube transcript fetching
│   ├── main.py           # Core business logic
│   └── metrics.py        # Usage tracking
└── frontend/             # React frontend (optional)
    └── ...
```

## 🚢 Deployment

### Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in Settings → Secrets:
   ```toml
   GOOGLE_API_KEY = "your_key"
   SUPABASE_URL = "your_url"
   SUPABASE_KEY = "your_key"
   DEFAULT_ADMIN_USERNAME = "admin"
   DEFAULT_ADMIN_PASSWORD = "secure_password"
   DEFAULT_ADMIN_EMAIL = "admin@example.com"
   ```
5. Deploy!

### Deploy with Docker

```bash
docker build -t youtube-rag-notetaker .
docker run -p 8501:8501 --env-file backend/.env youtube-rag-notetaker
```

## 🔒 Security Notes

- ✅ Passwords hashed with Argon2
- ✅ Row-level security in Supabase
- ✅ Environment variables for secrets
- ✅ Input validation and sanitization
- ⚠️ Change default admin password
- ⚠️ Use HTTPS in production
- ⚠️ Enable rate limiting

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🐛 Issues

Found a bug? [Open an issue](https://github.com/yourusername/youtube-rag-notetaker/issues)

## 📧 Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/youtube-rag-notetaker](https://github.com/yourusername/youtube-rag-notetaker)

## 🙏 Acknowledgments

- Google Gemini API
- Supabase
- ChromaDB
- Streamlit
- LangChain

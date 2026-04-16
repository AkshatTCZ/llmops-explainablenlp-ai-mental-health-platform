# AI Mental Health Platform - Frontend

A beautiful, responsive web interface for the AI Mental Health Chat system with emotion-aware responses.

## Features

- 🎨 Modern, responsive UI design
- 💬 Real-time chat interface
- 😊 Emotion detection and display
- 🔄 Conversation management
- 📱 Mobile-friendly responsive design
- ⚡ Fast and smooth interactions

## Setup Instructions

### 1. Install Node.js Dependencies

```bash
cd app
npm install
```

### 2. Make sure Python dependencies are installed

```bash
# From project root
pip install -r requirements.txt
```

### 3. Make sure Ollama is running

```bash
# Start Ollama server
ollama serve

# Make sure phi3 model is installed
ollama pull phi3
```

### 4. Start the Server

```bash
# From app directory
npm start

# Or for development with auto-reload
npm run dev
```

### 5. Open in Browser

Navigate to `http://localhost:3000`

## Project Structure

```
app/
├── server.js              # Node.js Express server
├── hybrid_chat_api.py     # Python API wrapper
├── package.json           # Node.js dependencies
├── public/
│   ├── index.html        # Main HTML file
│   ├── styles.css        # Styling
│   └── script.js         # Frontend JavaScript
└── README.md             # This file
```

## API Endpoints

- `POST /api/chat` - Send a message and get response
- `POST /api/reset` - Reset conversation
- `GET /api/health` - Health check

## Technologies Used

- **Backend**: Node.js, Express
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI**: Python, Transformers, Ollama (phi3)
- **Styling**: Custom CSS with modern design patterns

## Notes

- The system requires Ollama to be running locally
- The phi3 model must be installed in Ollama
- The DistilBERT emotion detection model must be trained (run `scripts/train.py`)







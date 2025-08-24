# Westfield Agent - Local Politics Intelligence

An intelligent agent powered by Google's ADK (Agent Development Kit) and Gemini that monitors social media (starting with Reddit) to understand local politics and issues in New Jersey, with a focus on Congressional District 07.

## Features

- **Reddit Data Collection**: Downloads and monitors r/newjersey for political content
- **Async Updates**: Continuously polls for new posts and comments
- **RAG Storage**: Vector database with semantic search using ChromaDB
- **Topic Analysis**: Categorizes content by political topics (elections, taxes, education, etc.)
- **Location Tracking**: Identifies mentions of NJ cities and counties
- **CLI Interface**: Rich command-line interface for all operations

## Setup

### 1. Install Dependencies

```bash
pip install -r agents/westfield/requirements.txt
```

### 2. Configure Reddit API

1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (script type)
3. Note your client ID and secret

### 3. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Reddit API credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=westfield-agent/1.0

# Optional: Data directory (defaults to ./data)
WESTFIELD_DATA_DIR=data
```

## Usage

### Running the Agent

The Westfield agent can be run using the interactive CLI:

#### CLI Interface (Interactive Chat)
```bash
python -m agents.westfield.app_cli
```

### Initial Data Setup

Before using the agent, you need to download initial Reddit data:

```bash
# Download the last 30 days of posts from r/newjersey
python -m agents.westfield.cli download --days 30 --with-comments

# Build the vector index
python -m agents.westfield.cli index
```

### Data Management CLI

The original CLI tools are still available for data management:

```bash
# Update with new posts
python -m agents.westfield.cli update

# Monitor continuously
python -m agents.westfield.cli monitor --interval 300

# Search the database
python -m agents.westfield.cli search "property taxes in Westfield"

# View statistics
python -m agents.westfield.cli stats
```

## CLI Commands

- `download` - Download initial data from Reddit
- `update` - Fetch new posts since last update  
- `monitor` - Continuously monitor for new posts
- `index` - Build/rebuild vector index
- `search` - Semantic search for content
- `search-topic` - Search by political topic
- `context` - Get RAG context for a query
- `stats` - Show statistics about stored data

## Data Structure

```
data/
├── reddit/
│   ├── posts/          # JSON files for each post
│   ├── comments/       # Comments organized by post ID
│   └── metadata/       # Download metadata
└── chroma/             # Vector database files
```

## Architecture

### ADK Integration

The Westfield agent uses Google's Agent Development Kit (ADK) with Gemini to provide intelligent analysis of Reddit data. It exposes four main tools:

- **reddit_search**: Live search of Reddit posts
- **vector_search**: Semantic search of indexed content
- **get_trending_topics**: Analysis of trending political topics
- **download_new_posts**: Update the database with new content

### Components

1. **Agent** (`agent.py`)
   - ADK-based agent using Gemini
   - Tool definitions for Reddit operations
   - RAG-based context retrieval

2. **Reddit Client** (`reddit/client.py`)
   - Async-compatible PRAW wrapper
   - Handles authentication and rate limiting
   - Supports streaming new posts

3. **Downloader** (`reddit/downloader.py`)
   - Initial bulk download
   - Incremental updates
   - Continuous monitoring

4. **Vector Store** (`storage/vector_store.py`)
   - ChromaDB for embeddings
   - Semantic search
   - Topic and location filtering

5. **Data Models** (`models/reddit_data.py`)
   - Structured data for posts/comments
   - Political topic categorization
   - Relevance scoring

## Political Topics Tracked

- Elections
- Taxes
- Education  
- Infrastructure
- Housing
- Environment
- Crime & Safety
- Healthcare
- Transportation
- Economy
- Social Issues
- Local Government
- State Politics

## Future Enhancements

- [ ] Add more social media sources (Twitter/X, Facebook groups)
- [ ] Sentiment analysis
- [ ] Entity extraction for politicians and organizations
- [ ] Issue tracking and trending analysis
- [ ] Integration with voter data for demographic insights
- [ ] Web UI for exploring data
- [ ] LLM-powered summarization of key issues

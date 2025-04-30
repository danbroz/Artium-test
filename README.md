# Academic Paper Search Agent

An AI-powered agent that searches and retrieves academic papers from various sources using natural language queries.

## Features

- Search across multiple academic sources (OpenAlex, arXiv)
- Natural language query processing
- Detailed paper information retrieval
- RESTful API interface
- Conversation memory for context-aware searches
- Reverse inverted-index function for complete abstracts

## Setup

1. Create a virtual environment:
```bash
python -m venv artium-test
source artium-test/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
OPENALEX_EMAIL=your_email@example.com  # Optional, for polite API usage
```

## Usage

1. Start the API server:
```bash
python src/main.py
```

2. The API will be available at `http://localhost:8000`

### API Endpoints

- `POST /search`: Search for papers
  ```json
  {
    "topic": "your search topic",
    "max_results": 10
  }
  ```

- `GET /paper/{paper_id}`: Get detailed information about a specific paper

## Project Structure

```
.
├── src/
│   ├── agents/
│   │   └── paper_search_agent.py
│   ├── config/
│   │   └── settings.py
│   ├── utils/
│   │   └── xml_parser.py
│   └── main.py
├── requirements.txt
└── README.md
```

## How It Works

1. **Paper Search**: The agent uses OpenAlex and arXiv APIs to search for academic papers based on user queries.

2. **Abstract Processing**: The system includes a reverse inverted-index function that converts abstracts from position-based format to complete text.

3. **Response Processing**: The agent processes API responses and extracts structured information about papers.

4. **Memory**: The system maintains conversation memory to provide context-aware responses.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

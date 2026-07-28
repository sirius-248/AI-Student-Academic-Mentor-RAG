# AI Student Academic Mentor - RAG System

An intelligent Retrieval Augmented Generation (RAG) system designed to help students learn and understand academic content through interactive mentoring.

## Features

- 📚 **PDF Document Processing**: Extract and process PDF documents for knowledge retrieval
- 🤖 **AI-Powered Tutoring**: Uses Azure OpenAI to provide intelligent, context-aware answers
- 🔍 **Retrieval Augmented Generation**: Combines document retrieval with LLM capabilities
- 📖 **Academic Support**: Specialized prompts for educational guidance and learning

## Project Structure

```
AI-Student-Academic-Mentor-RAG/
├── app/
│   ├── document_reader/      # PDF reading and processing
│   ├── llm/                  # Azure OpenAI integration
│   ├── prompts/              # Prompt management
│   ├── utils/                # Utility functions
│   └── main.py               # Application entry point
├── data/
│   └── sample_pdfs/          # Sample PDF documents
├── tests/                    # Unit tests
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Student-Academic-Mentor-RAG
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

## Usage

Run the main application:
```bash
python app/main.py
```

## Configuration

Set the following environment variables in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key
- `PDF_DATA_PATH`: Path to PDF documents
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure

- **document_reader**: Handles PDF parsing and text extraction
- **llm**: Azure OpenAI client and LLM interactions
- **prompts**: Prompt templates and management
- **utils**: Helper functions and utilities

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## Support

For issues and questions, please open an issue in the repository.

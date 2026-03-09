# Clarity OS T4 - Module A: Local Search + Summarize with Citations

A local knowledge search assistant for founders/SBOs that provides read-only filesystem search and document parsing with verifiable citations.

## Features

- **Local Search**: Search across documents, code, and data files
- **Citation-Based Answers**: Every answer includes file paths and snippets
- **Structured Coverage**: Detailed reports on search scope and results
- **Read-Only Operations**: No file modifications, completely safe
- **Multi-Format Support**: Text, code, CSV, DOCX, PDF files
- **Safety Controls**: Built-in limits and secret redaction

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI available (optional)
export PATH=$PATH:$(pwd)
```

## Usage

### Search Command
```bash
python -m clarity.main search --root /path/to/docs --query "search term" \
  --globs "**/*.md,**/*.docx" --case-sensitive --context 3
```

### Ask Command (Search + Summarize)
```bash
python -m clarity.main ask --root /path/to/docs --question "What are our policies?" \
  --globs "**/*.txt,**/*.md" --max-files 1000
```

### Sources Command
```bash
python -m clarity.main sources --last
```

### Health Check
```bash
python -m clarity.main health
```

## Supported File Types

- **Text**: .txt, .md, .log
- **Code/Config**: .py, .js, .ts, .json, .yaml/.yml, .toml, .ini
- **Data**: .csv
- **Documents**: .docx, .pdf (best-effort)

## Safety Features

- **Hard Limits**: Configurable limits on files, matches, and file sizes
- **Allowlisted Roots**: Optional restriction to approved directories
- **Secret Redaction**: Automatic redaction of API keys, passwords, tokens
- **Read-Only**: No write, move, or delete operations

## Configuration

Environment variables:
```bash
export CLARITY_BOOT_DOC_PATH="/path/to/boot/document.md"
export CLARITY_MAX_FILES="5000"
export CLARITY_MAX_MATCHES="2000"
export CLARITY_MAX_FILE_SIZE="10485760"  # 10MB
export CLARITY_ALLOWLISTED_ROOTS="/path/to/docs,/another/path"
```

## Response Format

All responses include:
- **Answer**: Concise response to the query
- **Citations**: (file_path, location, snippet) tuples
- **Coverage**: Search scope, limits, counts, skipped files
- **Confidence**: low/med/high with reasoning

## Architecture

- **Local Search Toolkit**: 6 core read-only file operations
- **CLI Commands**: search, ask, sources, health
- **Response Formatter**: Structured output with citations
- **Safety Layer**: Limits, redaction, validation

## Development

```bash
# Run tests (when implemented)
python -m pytest tests/

# Format code
black clarity/

# Lint code
flake8 clarity/
```

## License

# SQL Query Anonymizer

A Python tool for anonymizing SQL queries while preserving their structure and maintaining the ability to de-anonymize them later. Perfect for query optimization workflows, security testing, or data sharing scenarios where you need to hide sensitive identifiers.

## ✨ Features

- **🔒 Anonymization**: Replace table names, column names, and literals with generic placeholders
- **🔓 De-anonymization**: Restore original identifiers from anonymized queries
- **💾 Persistent Mappings**: Pickle-based storage maintains mappings across sessions
- **🎯 Structure Preservation**: SQL syntax and query structure remain intact
- **📊 Table Alias Detection**: Quantifies table aliases in SELECT statements
- **🔄 Roundtrip Guarantee**: Perfect roundtrip anonymization ↔ de-anonymization
- **🖥️ CLI & Python API**: Use via command-line or import in Python code
- **📁 File Processing**: Process SQL files in batch
- **🧪 Comprehensive Tests**: 73 passing tests with pytest

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/ncarsner/sql-query-anonymizer.git
cd sql-query-anonymizer

# Install dependencies (using uv)
uv sync

# Or using pip
pip install -e .

# After installation, the sql-anonymizer command will be available
sql-anonymizer --help
```

## 🚀 Quick Start

### Command Line Interface

```bash
# Anonymize a SQL query
sql-anonymizer anonymize "SELECT name, email FROM users WHERE age > 25"
# Output: SELECT identifier_1 , identifier_2 FROM table_1 WHERE identifier_3 > literal_1

# De-anonymize back to original
sql-anonymizer deanonymize "SELECT identifier_1 , identifier_2 FROM table_1 WHERE identifier_3 > literal_1"
# Output: SELECT name , email FROM users WHERE age > 25

# Show current mappings
sql-anonymizer show-mappings

# Process SQL files
sql-anonymizer anonymize -f input.sql -o anonymized.sql
```

### Python API

```python
from src.sql_query_anonymizer.utils import Anonymizer

# Create an anonymizer instance with default mapping file
anonymizer = Anonymizer()

# Anonymize a query
original = "SELECT customer_id, name FROM customers WHERE age > 30"
anonymized = anonymizer.anonymize_query(original)
print(anonymized)  # SELECT identifier_1 , identifier_2 FROM table_1 WHERE identifier_3 > literal_1

# Save mappings to persist for later
anonymizer.save()

# Later session - create new anonymizer and load mappings
anonymizer2 = Anonymizer()
anonymizer2.load()

# De-anonymize back to original
restored = anonymizer2.de_anonymize_query(anonymized)
print(restored)  # SELECT customer_id , name FROM customers WHERE age > 30

# Or use context manager for automatic save/load
with Anonymizer() as anon:
    anonymized = anon.anonymize_query(original)
    # Mappings automatically saved on exit
```

## 📁 Project Structure

```
sql-query-anonymizer/
├── src/
│   └── sql_query_anonymizer/
│       ├── __init__.py
│       ├── anonymize.py          # Anonymization preprocessing
│       ├── cli.py                # Command-line interface
│       ├── constants.py          # SQL keywords and configuration
│       ├── helper_utilities.py   # File I/O utilities
│       ├── tokenize.py           # SQL tokenization engine
│       └── utils.py              # Core Anonymizer class
├── tests/
│   ├── test_anonymize.py         # Anonymization tests
│   ├── test_cli.py               # CLI tests
│   ├── test_tokenize.py          # Tokenization tests
│   └── test_utils.py             # Core utilities tests
├── data/
│   ├── 0_raw/                    # Sample raw SQL files
│   ├── 1_anonymized/             # Anonymized outputs
│   ├── 2_optimized/              # Optimized queries
│   └── 3_deanonymized/           # De-anonymized outputs
├── pyproject.toml                # Project configuration
├── README.md
└── LICENSE
```

## 🎯 Use Cases

1. **Query Optimization**: Anonymize queries before sending to external optimization services
2. **Security Testing**: Share query structures without exposing sensitive database schema
3. **Documentation**: Create generic examples from real queries
4. **Training**: Generate training datasets with anonymized queries
5. **Debugging**: Share problematic queries with support teams without revealing confidential data

## 🔧 CLI Commands

| Command | Description |
|---------|-------------|
| `anonymize` | Anonymize SQL query from string or file |
| `deanonymize` | De-anonymize query back to original form |
| `show-mappings` | Display current mapping statistics |
| `clear-mappings` | Clear all stored mappings |
| `export-mappings` | Export mappings to another pickle file |
| `import-mappings` | Import mappings from a pickle file |
| `interactive` | Start interactive mode |

**Examples:**
```bash
# Anonymize a query
sql-anonymizer anonymize "SELECT * FROM users"

# Show current mappings
sql-anonymizer show-mappings

# Export mappings for backup
sql-anonymizer export-mappings backup.pkl

# Use custom mapping file
sql-anonymizer -m custom.pkl anonymize "SELECT * FROM products"
```

## 💾 Persistent Storage

Mappings are stored as pickle files in `~/.sql_anonymizer/mappings.pkl` and persist across sessions. This ensures:

- **Consistent anonymization**: Same identifiers always map to the same placeholders
- **Session persistence**: Mappings survive between CLI sessions
- **Backup and restore**: Export/import mappings as needed
- **Context manager support**: Automatic save/load using Python's `with` statement

The pickle format stores mappings, reverse mappings, and counters efficiently.

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/sql_query_anonymizer

# Run specific test file
uv run pytest tests/test_utils.py

# Run with verbose output
uv run pytest -v
```

## 📋 Requirements

- Python 3.13+
- pytest (for testing)
- pytest-cov (for coverage reports)

## 🔍 How It Works

1. **Tokenization**: SQL query is parsed into tokens (keywords, identifiers, literals, operators)
2. **Classification**: Tokens are classified by type (table names, column names, literals, etc.)
3. **Mapping**: Each unique identifier is mapped to a generic placeholder
4. **Replacement**: Original identifiers are replaced with placeholders
5. **Persistence**: Mappings are saved for future de-anonymization
6. **De-anonymization**: Placeholders are mapped back to original identifiers

## 🎨 Example Transformations

```sql
-- Original
SELECT c.customer_id, c.first_name, o.order_date, SUM(o.amount)
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE c.status = 'active' AND o.date >= '2024-01-01'
GROUP BY c.customer_id, c.first_name, o.order_date;

-- Anonymized
SELECT c.identifier_1 , c.identifier_2 , o.identifier_3 , SUM ( o.identifier_4 )
FROM table_1 c
JOIN table_2 o ON c.identifier_1 = o.identifier_1
WHERE c.identifier_5 = literal_1 AND o.identifier_6 >= literal_2
GROUP BY c.identifier_1 , c.identifier_2 , o.identifier_3 ;
```

## 🛠️ Configuration

**Custom mapping file location:**
```bash
sql-anonymizer -m custom_mappings.pkl anonymize "SELECT * FROM users"
```

**Disable auto-save:**
```bash
sql-anonymizer --no-auto-save anonymize "SELECT * FROM users"
```

**Python API with custom location:**
```python
# Use custom mapping file
anonymizer = Anonymizer(mapping_file="project_mappings.pkl")
anonymizer.load()  # Load existing mappings

# Or use absolute path
anonymizer = Anonymizer(mapping_file="/path/to/mappings.pkl")
```

## 🔍 Feature Status

### ✅ Completed
- [x] Core anonymization/de-anonymization engine
- [x] Pickle-based persistent mapping storage
- [x] Context manager support (`with` statement)
- [x] Command-line interface with multiple commands
- [x] File processing capabilities
- [x] Table alias detection and quantification
- [x] Comprehensive test suite (73 passing tests)
- [x] Export/import functionality

### 🚧 Future Enhancements
- [ ] Support for additional SQL dialects (PostgreSQL, MySQL, etc.)
- [ ] GUI interface
- [ ] API server mode
- [ ] Pattern-based anonymization rules
- [ ] Integration with query optimization tools
- [ ] Publish to PyPI

## 🧾 License

MIT License - See [LICENSE](LICENSE) for details

## ✍️ Author

Developed by Nicholas Carsner

Contributions, issues, and feature requests are welcome!

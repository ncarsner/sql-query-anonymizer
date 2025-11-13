# SQL Query Anonymizer - CLI Usage Guide

## Overview

The SQL Query Anonymizer provides a comprehensive command-line interface for anonymizing SQL queries while preserving their structure and maintaining persistent mappings for de-anonymization.

## Installation & Setup

```bash
# Install the package (if using pip)
pip install -e .

# Or run directly from the repository
python -m src.sql_query_anonymizer.cli --help
```

## Key Features

- **Persistent Mappings**: Automatically saves and loads mappings between sessions
- **Multiple Storage Options**: Use default location or specify custom mapping files
- **File Processing**: Process entire SQL files or individual queries
- **Interactive Mode**: Command-line interface for exploratory work
- **Import/Export**: Backup and share mapping configurations

## Default Mapping Storage

By default, mappings are stored in `~/.sql_anonymizer/mappings.json` and are automatically:
- **Loaded** when starting a new session (if the file exists)
- **Saved** whenever new mappings are created (auto-save mode)
- **Preserved** across different CLI sessions

## Command Structure

```bash
sql-anonymizer [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Options
- `-m, --mapping-file PATH`: Use custom mapping file location
- `--no-auto-save`: Disable automatic saving of mappings
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help information

## Commands

### 1. Anonymize Queries

**Anonymize a query string:**
```bash
sql-anonymizer anonymize "SELECT name, email FROM users WHERE id = 1"
```

**Anonymize a SQL file:**
```bash
sql-anonymizer anonymize -f input_query.sql -o anonymized_query.sql
```

**Use custom mapping file:**
```bash
sql-anonymizer -m project_mappings.json anonymize "SELECT * FROM customers"
```

### 2. De-anonymize Queries

**De-anonymize a query:**
```bash
sql-anonymizer deanonymize "SELECT identifier_1 FROM table_1 WHERE identifier_2 = literal_1"
```

**De-anonymize from file:**
```bash
sql-anonymizer deanonymize -f anonymized.sql -o original.sql
```

### 3. Mapping Management

**Show current mappings:**
```bash
sql-anonymizer show-mappings
```

**Clear all mappings:**
```bash
sql-anonymizer clear-mappings
```

**Export mappings:**
```bash
sql-anonymizer export-mappings backup_mappings.json
```

**Import mappings:**
```bash
sql-anonymizer import-mappings backup_mappings.json
```

### 4. Interactive Mode

**Start interactive session:**
```bash
sql-anonymizer interactive
```

In interactive mode, you can use these commands:
- `anonymize <query>` - Anonymize a SQL query
- `deanonymize <query>` - De-anonymize a query
- `show-mappings` - Display mapping statistics
- `clear-mappings` - Clear all mappings
- `export <file>` - Export mappings to file
- `import <file>` - Import mappings from file
- `help` - Show available commands
- `quit` - Exit interactive mode

## Usage Examples

### Example 1: Basic Workflow

```bash
# Anonymize a query (creates/updates mappings)
sql-anonymizer anonymize "SELECT c.name, o.total FROM customers c JOIN orders o ON c.id = o.customer_id"

# Result: SELECT c.identifier_1 , o.identifier_2 FROM table_1 c JOIN table_2 o ON c.identifier_3 = o.identifier_4

# Check what mappings were created
sql-anonymizer show-mappings

# De-anonymize the result
sql-anonymizer deanonymize "SELECT c.identifier_1 , o.identifier_2 FROM table_1 c JOIN table_2 o ON c.identifier_3 = o.identifier_4"
```

### Example 2: Project-Specific Mappings

```bash
# Use project-specific mapping file
PROJECT_MAPPINGS="./project_mappings.json"

# Anonymize multiple queries for the same project
sql-anonymizer -m $PROJECT_MAPPINGS anonymize "SELECT * FROM users"
sql-anonymizer -m $PROJECT_MAPPINGS anonymize "SELECT * FROM orders"  # Reuses 'users' if referenced

# Export project mappings for sharing
sql-anonymizer -m $PROJECT_MAPPINGS export-mappings shared_mappings.json
```

### Example 3: File Processing

```bash
# Process a large SQL file
sql-anonymizer anonymize -f complex_query.sql -o anonymized_query.sql

# Later, after optimization, de-anonymize
sql-anonymizer deanonymize -f optimized_anonymized.sql -o final_query.sql
```

### Example 4: Backup and Restore

```bash
# Backup current mappings
sql-anonymizer export-mappings backup_$(date +%Y%m%d).json

# Clear mappings for fresh start
sql-anonymizer clear-mappings

# Later, restore from backup
sql-anonymizer import-mappings backup_20241031.json
```

## Mapping File Format

The mapping files are JSON format containing:

```json
{
  "mappings": {
    "TokenType.IDENTIFIER": {"name": "identifier_1", "email": "identifier_2"},
    "TokenType.TABLE": {"users": "table_1", "orders": "table_2"},
    "TokenType.LITERAL": {"1": "literal_1", "'active'": "literal_2"}
  },
  "reverse_mappings": {
    "TokenType.IDENTIFIER": {"identifier_1": "name", "identifier_2": "email"},
    "TokenType.TABLE": {"table_1": "users", "table_2": "orders"},
    "TokenType.LITERAL": {"literal_1": "1", "literal_2": "'active'"}
  },
  "counters": {
    "TokenType.IDENTIFIER": 2,
    "TokenType.TABLE": 2,
    "TokenType.LITERAL": 2
  }
}
```

## Integration with Query Optimizers

The CLI is designed to work seamlessly with SQL query optimizers:

1. **Anonymize** your sensitive queries
2. **Send anonymized queries** to external optimizers
3. **Receive optimized anonymized queries** back
4. **De-anonymize** to get optimized queries with original identifiers

```bash
# Step 1: Anonymize
sql-anonymizer anonymize -f sensitive_query.sql -o anonymized_for_optimizer.sql

# Step 2: External optimizer processes anonymized_for_optimizer.sql
# (Creates optimized_anonymized.sql)

# Step 3: De-anonymize the optimized result
sql-anonymizer deanonymize -f optimized_anonymized.sql -o final_optimized_query.sql
```

## Troubleshooting

**Mappings not persisting:**
- Check file permissions in `~/.sql_anonymizer/`
- Use `--verbose` flag to see detailed operations
- Verify auto-save is enabled (default)

**Cannot find previous mappings:**
- Ensure you're using the same mapping file location
- Use `sql-anonymizer show-mappings` to verify current state
- Check if mappings were exported to a different file

**Errors with custom mapping files:**
- Ensure the directory exists and is writable
- Use absolute paths for mapping files
- Verify JSON format if importing existing mappings

## Performance Tips

- **Reuse mapping files** for related queries in the same project
- **Export mappings** before major changes for backup
- **Use custom mapping files** for different projects to avoid conflicts
- **Interactive mode** is efficient for exploratory work with multiple queries
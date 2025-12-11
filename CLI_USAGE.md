# CLI Quick Reference

A focused reference for using the SQL Query Anonymizer command-line interface.

For complete documentation, see [README.md](README.md).

> **Note:** After installing the package with `pip install -e .` or `uv sync`, the `sql-anonymizer` command will be available in your terminal.

## Quick Start

```bash
# Run CLI
sql-anonymizer --help

# Anonymize a query
sql-anonymizer anonymize "SELECT name FROM users"

# De-anonymize a query
sql-anonymizer deanonymize "SELECT identifier_1 FROM table_1"
```

## Default Storage

Mappings are stored as pickle files in `~/.sql_anonymizer/mappings.pkl`:
- **Auto-loaded** when CLI starts (if file exists)
- **Auto-saved** after anonymization operations
- **Persistent** across CLI sessions

## Command Structure

```bash
sql-anonymizer [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Options
- `-m, --mapping-file PATH`: Use custom mapping file (must be `.pkl` file)
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
sql-anonymizer -m project_mappings.pkl anonymize "SELECT * FROM customers"
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
sql-anonymizer export-mappings backup_mappings.pkl
```

**Import mappings:**
```bash
sql-anonymizer import-mappings backup_mappings.pkl
```

### 4. Interactive Mode

**Start interactive session:**
```bash
sql-anonymizer interactive
```

Interactive mode provides a REPL-like experience for working with multiple queries.

## Usage Examples

### Example 1: Basic Workflow

```bash
# Anonymize a query (creates/updates mappings)
sql-anonymizer anonymize "SELECT c.name, o.total FROM customers c JOIN orders o ON c.id = o.customer_id"
# Output: SELECT c.identifier_1 , o.identifier_2 FROM table_1 c JOIN table_2 o ON c.identifier_3 = o.identifier_4

# Check what mappings were created
sql-anonymizer show-mappings

# De-anonymize the result
sql-anonymizer deanonymize "SELECT c.identifier_1 , o.identifier_2 FROM table_1 c JOIN table_2 o ON c.identifier_3 = o.identifier_4"
# Output: SELECT c.name , o.total FROM customers c JOIN orders o ON c.id = o.customer_id
```

### Example 2: Project-Specific Mappings

```bash
# Use project-specific mapping file
PROJECT_MAPPINGS="./project_mappings.pkl"

# Anonymize multiple queries for the same project
sql-anonymizer -m $PROJECT_MAPPINGS anonymize "SELECT * FROM users"
sql-anonymizer -m $PROJECT_MAPPINGS anonymize "SELECT * FROM orders"

# Export project mappings for sharing
sql-anonymizer -m $PROJECT_MAPPINGS export-mappings shared_mappings.pkl
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
sql-anonymizer export-mappings backup_$(date +%Y%m%d).pkl

# Clear mappings for fresh start
sql-anonymizer clear-mappings

# Later, restore from backup
sql-anonymizer import-mappings backup_20241210.pkl
```

## Mapping File Format

Mapping files use Python's pickle format (`.pkl`) containing:
- **mappings**: Dictionary of original identifiers → placeholders (by token type)
- **reverse_mappings**: Dictionary of placeholders → original identifiers (for de-anonymization)
- **counters**: Current counter values for each token type

The pickle format provides:
- **Efficient serialization** of Python objects
- **Type preservation** (no need to parse enums)
- **Fast load/save** operations

Note: Pickle files are Python-specific and not human-readable. For sharing across languages, use export/import to create portable files.

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
- Verify the file is a valid pickle file (`.pkl` extension)
- Pickle files are Python version-specific; regenerate if needed

## Performance Tips

- **Reuse mapping files** for related queries in the same project
- **Export mappings** before major changes for backup
- **Use custom mapping files** for different projects to avoid conflicts
- **Interactive mode** is efficient for exploratory work with multiple queries

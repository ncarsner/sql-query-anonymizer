import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import List
import json
import os

from .constants import ALL_SQL_FUNCTIONS, OP_PATTERN, SQL_KEYWORDS
from .helper_utilities import read_sql_file


class TokenType(Enum):
    FUNCTION = auto()
    KEYWORD = auto()
    TABLE = auto()
    TABLE_ALIAS = auto()
    IDENTIFIER = auto()
    IDENTIFIER_ALIAS = auto()
    LITERAL = auto()
    SYMBOL = auto()
    WHITESPACE = auto()
    COMMENT = auto()
    UNKNOWN = auto()


TYPE_PREFIXES = {TokenType.TABLE, TokenType.IDENTIFIER, TokenType.LITERAL}


@dataclass
class Token:
    type: TokenType
    value: str
    space: bool = False


class Anonymizer:
    """A class to anonymize SQL identifiers (table names, column names, literals) in a SQL query while preserving SQL keywords and functions.
    Usage:
        anonymizer = Anonymizer()
        anonymized_query = anonymizer.anonymize(sql_query)
    Methods:
        - __init__: Initializes the anonymizer with empty mappings and counters.
        - _prefix: Returns the prefix string for a given token type.
        - get: Returns the placeholder for a given identifier, creating a new one if it's not already mapped.
        - anonymize: Takes a SQL query string, tokenizes it, and replaces identifiers with their placeholders.
    """

    def __init__(self, mapping_file: str | None = None, auto_save: bool = True):
        self.mappings: dict[TokenType, dict[str, str]] = defaultdict(dict)
        self.counters: dict[TokenType, int] = Counter()
        self.reverse_mappings: dict[TokenType, dict[str, str]] = defaultdict(dict)
        
        # CLI and persistence settings  
        # Special case: if mapping_file is explicitly the string "NONE", disable persistence for tests
        if mapping_file is None:
            self.mapping_file = None
            self.auto_save = False
            load_existing = False
        else:
            self.mapping_file = mapping_file if mapping_file is not None else self._get_default_mapping_file()
            self.auto_save = auto_save
            load_existing = True
        
        # Load existing mappings if persistence is enabled and file exists
        if load_existing and self.mapping_file and os.path.exists(self.mapping_file):
            try:
                self.load_mappings_from_json(self.mapping_file)
                print(f"Loaded existing mappings from: {self.mapping_file}")
            except Exception as e:
                print(f"Warning: Could not load mappings from {self.mapping_file}: {e}")
                
    def _get_default_mapping_file(self) -> str:
        """Get the default mapping file location."""
        # Create a .sql_anonymizer directory in user's home for storing mappings
        home_dir = os.path.expanduser("~")
        mapping_dir = os.path.join(home_dir, ".sql_anonymizer")
        
        # Create directory if it doesn't exist
        os.makedirs(mapping_dir, exist_ok=True)
        
        return os.path.join(mapping_dir, "mappings.json")

    def _prefix(self, token_type: TokenType):
        type_prefixes = {
            TokenType.TABLE: "table",
            TokenType.IDENTIFIER: "identifier",
            TokenType.LITERAL: "literal",
        }
        if token_type not in type_prefixes:
            raise ValueError(f"Unsupported token type: {token_type}")
        return type_prefixes[token_type]

    def get_or_assign(self, identifier: str, token_type: TokenType) -> str:
        # DEBUG: print the identifier and token type being processed
        print(f"Identifier: {identifier}, Type: {token_type}")

        # Special handling for aliases - return as-is
        if token_type is TokenType.TABLE_ALIAS:
            # Check if this alias was already created from a table/identifier
            for table_mapping in self.mappings[TokenType.TABLE].values():
                if identifier.lower() == table_mapping.split("_")[0].lower():
                    return identifier  # Return original alias
            return identifier

        m = self.mappings[token_type]
        if identifier in m:
            return m[identifier]

        self.counters[token_type] += 1
        prefix = f"{self._prefix(token_type)}_{self.counters[token_type]}"
        m[identifier] = prefix

        self.reverse_mappings[token_type][prefix] = identifier

        return prefix

    def anonymize_query(self, query: str) -> str:
        tokens = tokenize_sql(query)

        anonymized_tokens = []
        mappings_changed = False
        
        for token in tokens:
            if token.type in TYPE_PREFIXES:
                original_count = sum(self.counters.values())
                anonymized_value = self.get_or_assign(token.value, token.type)
                
                # Check if new mapping was created
                if sum(self.counters.values()) > original_count:
                    mappings_changed = True
                    
                anonymized_tokens.append(
                    Token(token.type, anonymized_value, token.space)
                )
            else:
                anonymized_tokens.append(token)

        # Auto-save mappings if they changed and auto_save is enabled
        if mappings_changed and self.auto_save:
            self._save_mappings_safely()

        return " ".join(token.value for token in anonymized_tokens)

    def de_anonymize_query(self, anonymized_query: str) -> str:
        tokens = tokenize_sql(anonymized_query)

        de_anonymized_tokens = []
        for token in tokens:
            # Check if this token value exists in any of the reverse mappings
            original_value = None
            original_type = None

            # Check all TYPE_PREFIXES for the token value, regardless of current token type
            for check_type in TYPE_PREFIXES:
                if token.value in self.reverse_mappings[check_type]:
                    original_value = self.reverse_mappings[check_type][token.value]
                    original_type = check_type
                    break

            if original_value is not None and original_type is not None:
                de_anonymized_tokens.append(
                    Token(original_type, original_value, token.space)
                )
            else:
                de_anonymized_tokens.append(token)

        return " ".join(token.value for token in de_anonymized_tokens)

    def save_mappings_to_json(self, filepath: str) -> None:
        mappings_data = {
            "mappings": {str(k): v for k, v in self.mappings.items()},
            "reverse_mappings": {str(k): v for k, v in self.reverse_mappings.items()},
            "counters": {str(k): v for k, v in self.counters.items()},
        }

        with open(filepath, "w") as f:
            json.dump(mappings_data, f, indent=2)

    def load_mappings_from_json(self, filepath: str) -> None:
        with open(filepath, "r") as f:
            loaded_data = json.load(f)

        # Clear existing mappings
        self.mappings = defaultdict(dict)
        self.reverse_mappings = defaultdict(dict)
        self.counters = Counter()

        # Convert string keys back to TokenType
        for token_type_str, mapping in loaded_data["mappings"].items():
            token_type = getattr(TokenType, token_type_str.split(".")[1])
            self.mappings[token_type] = mapping

        for token_type_str, mapping in loaded_data["reverse_mappings"].items():
            token_type = getattr(TokenType, token_type_str.split(".")[1])
            self.reverse_mappings[token_type] = mapping

        for token_type_str, count in loaded_data["counters"].items():
            token_type = getattr(TokenType, token_type_str.split(".")[1])
            self.counters[token_type] = count

    def serialize_anonymized_query(self, original_query: str, anonymized_query: str, filepath: str) -> None:
        """
        Serialize an anonymized query with its mappings for later recall and optimization.
        
        Args:
            original_query: The original SQL query
            anonymized_query: The anonymized version of the query
            filepath: Path to save the serialized data
        """
        serialized_data = {
            "original_query": original_query,
            "anonymized_query": anonymized_query,
            "mappings": {str(k): v for k, v in self.mappings.items()},
            "reverse_mappings": {str(k): v for k, v in self.reverse_mappings.items()},
            "counters": {str(k): v for k, v in self.counters.items()},
            "metadata": {
                "timestamp": self._get_timestamp(),
                "version": "1.0",
                "table_aliases": self._extract_table_aliases_info(anonymized_query)
            }
        }
        
        with open(filepath, "w") as f:
            json.dump(serialized_data, f, indent=2)

    def deserialize_and_decode(self, filepath: str) -> dict:
        """
        Deserialize anonymized query data and provide decoding capabilities.
        
        Args:
            filepath: Path to the serialized data file
            
        Returns:
            Dictionary containing original query, anonymized query, and decoding functions
        """
        with open(filepath, "r") as f:
            data = json.load(f)
        
        # Restore mappings
        self.mappings = defaultdict(dict)
        self.reverse_mappings = defaultdict(dict)
        self.counters = Counter()
        
        for token_type_str, mapping in data["mappings"].items():
            token_type = getattr(TokenType, token_type_str.split(".")[1])
            self.mappings[token_type] = mapping
            
        for token_type_str, mapping in data["reverse_mappings"].items():
            token_type = getattr(TokenType, token_type_str.split(".")[1])
            self.reverse_mappings[token_type] = mapping
            
        for token_type_str, count in data["counters"].items():
            token_type = getattr(TokenType, token_type_str.split(".")[1])
            self.counters[token_type] = count
        
        return {
            "original_query": data["original_query"],
            "anonymized_query": data["anonymized_query"],
            "metadata": data.get("metadata", {}),
            "decode_query": lambda query: self.de_anonymize_query(query),
            "decode_partial": lambda text: self._decode_partial_text(text),
            "get_mapping": lambda token_type, value: self.reverse_mappings.get(token_type, {}).get(value),
            "table_aliases": data.get("metadata", {}).get("table_aliases", [])
        }

    def process_optimized_query(self, optimized_anonymized_query: str) -> str:
        """
        Process an optimized anonymized query and decode it back to original identifiers.
        
        This method is specifically designed to handle queries that have been optimized
        while in their anonymized state, then decode them back to use original names.
        
        Args:
            optimized_anonymized_query: The optimized query with anonymized identifiers
            
        Returns:
            The optimized query with original identifiers restored
        """
        return self.de_anonymize_query(optimized_anonymized_query)

    def get_table_aliases_quantification(self, query: str) -> dict:
        """
        Quantify and return information about table aliases that precede periods in the query.
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Dictionary with alias quantification information
        """
        tokens = tokenize_sql(query)
        aliases_before_periods = {}
        table_aliases_found = set()
        
        # Debug: print tokens to see structure
        # for i, token in enumerate(tokens):
        #     print(f"{i}: {token.type} -> '{token.value}'")
        
        for i, token in enumerate(tokens):
            # Look for pattern: IDENTIFIER followed by SYMBOL "."
            if (
                token.type in [TokenType.IDENTIFIER, TokenType.TABLE_ALIAS]
                and i + 1 < len(tokens)
                and tokens[i + 1].type == TokenType.SYMBOL
                and tokens[i + 1].value == "."
            ):
                alias = token.value
                if alias not in aliases_before_periods:
                    aliases_before_periods[alias] = 0
                aliases_before_periods[alias] += 1
                
                # Mark as table alias if not already marked
                if token.type == TokenType.IDENTIFIER:
                    table_aliases_found.add(alias)
        
        return {
            "aliases_count": len(aliases_before_periods),
            "aliases": aliases_before_periods,
            "total_references": sum(aliases_before_periods.values()),
            "table_aliases_detected": list(table_aliases_found)
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        import datetime
        return datetime.datetime.now().isoformat()

    def _extract_table_aliases_info(self, query: str) -> list:
        """Extract information about table aliases from a query."""
        tokens = tokenize_sql(query)
        aliases = []
        
        for token in tokens:
            if token.type == TokenType.TABLE_ALIAS:
                aliases.append(token.value)
                
        return list(set(aliases))  # Remove duplicates

    def _decode_partial_text(self, text: str) -> str:
        """
        Decode partial anonymized text - useful for decoding individual identifiers.
        """
        # Check if the text matches any anonymized pattern
        for token_type in TYPE_PREFIXES:
            if text in self.reverse_mappings[token_type]:
                return self.reverse_mappings[token_type][text]
        return text  # Return original if not found in mappings

    def _save_mappings_safely(self) -> bool:
        """
        Safely save mappings to the default file with error handling.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if self.mapping_file is None:
            return False
        try:
            self.save_mappings_to_json(self.mapping_file)
            return True
        except Exception as e:
            print(f"Warning: Could not save mappings to {self.mapping_file}: {e}")
            return False

    def clear_mappings(self) -> None:
        """Clear all mappings from memory and optionally from file."""
        self.mappings = defaultdict(dict)
        self.reverse_mappings = defaultdict(dict)
        self.counters = Counter()
        
        if self.auto_save:
            self._save_mappings_safely()

    def export_mappings(self, filepath: str) -> bool:
        """
        Export current mappings to a specified file.
        
        Args:
            filepath: Path to export the mappings
            
        Returns:
            bool: True if exported successfully, False otherwise
        """
        try:
            self.save_mappings_to_json(filepath)
            print(f"Mappings exported to: {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting mappings: {e}")
            return False

    def import_mappings(self, filepath: str) -> bool:
        """
        Import mappings from a specified file.
        
        Args:
            filepath: Path to import mappings from
            
        Returns:
            bool: True if imported successfully, False otherwise
        """
        try:
            self.load_mappings_from_json(filepath)
            print(f"Mappings imported from: {filepath}")
            
            # Save to default location if auto_save is enabled
            if self.auto_save:
                self._save_mappings_safely()
            return True
        except Exception as e:
            print(f"Error importing mappings: {e}")
            return False

    def get_mapping_stats(self) -> dict:
        """
        Get statistics about current mappings.
        
        Returns:
            dict: Statistics about mappings
        """
        stats = {
            "mapping_file": self.mapping_file,
            "auto_save": self.auto_save,
            "total_mappings": sum(len(mappings) for mappings in self.mappings.values()),
            "by_type": {}
        }
        
        for token_type, mappings in self.mappings.items():
            if mappings:  # Only include non-empty mappings
                stats["by_type"][str(token_type)] = {
                    "count": len(mappings),
                    "counter_value": self.counters.get(token_type, 0)
                }
        
        return stats

    def set_mapping_file(self, filepath: str) -> None:
        """
        Set a new mapping file location.
        
        Args:
            filepath: New path for storing mappings
        """
        self.mapping_file = filepath
        print(f"Mapping file set to: {filepath}")

    def toggle_auto_save(self) -> bool:
        """
        Toggle auto-save functionality.
        
        Returns:
            bool: New auto_save state
        """
        self.auto_save = not self.auto_save
        print(f"Auto-save {'enabled' if self.auto_save else 'disabled'}")
        return self.auto_save


def normalize_casing(text: str) -> str:
    def ignore_within_quotes(match):
        return match.group(0)

    # Regex to match text outside quotes
    pattern = r"""
        (?<!\\)            # Negative lookbehind to ensure no backslash precedes
        "(?:\\.|[^"\\])*"  # Match double-quoted strings, allowing escaped quotes
        |                  # OR
        '(?:\\.|[^'\\])*'  # Match single-quoted strings, allowing escaped quotes
        |                  # OR
        ([^'"]+)           # Match any text outside quotes
    """
    return re.sub(
        pattern,
        lambda m: (
            ignore_within_quotes(m)
            if m.group(0).startswith(("'", '"'))
            else m.group(0).lower()
        ),
        text,
        flags=re.VERBOSE,
    )


def collapse_extra_spaces(text: str) -> str:
    return " ".join(re.split(r"\s+", text.strip()))


def normalize_keyword_casing(text: str) -> str:
    sorted_keywords = sorted(SQL_KEYWORDS | ALL_SQL_FUNCTIONS, key=len, reverse=True)
    pattern = r"\b(?:" + "|".join(map(re.escape, sorted_keywords)) + r")\b"
    return re.sub(pattern, lambda m: m.group(0).upper(), text, flags=re.IGNORECASE)


def tokenize_sql(query: str) -> List[Token]:
    """
    Tokenizes a given SQL query string into a list of tokens, such as keywords, identifiers, symbols, literals,
    and whitespace. Each identified component is returned as a `Token` object.
    Token Types:
        - TokenType.FUNCTION: SQL functions (e.g., COUNT, SUM, UPPER).
        - TokenType.KEYWORD: Whole word SQL keywords (e.g., SELECT, FROM, WHERE).
        - TokenType.TABLE: Table names following the FROM keyword.
        - TokenType.TABLE_ALIAS: Table aliases used in the query.
        - TokenType.IDENTIFIER: Identifiers such as table or column names.
        - TokenType.IDENTIFIER_ALIAS: Aliases for columns.
        - TokenType.LITERAL: String and numeric literals.
        - TokenType.SYMBOL: Operators and punctuation outside of quotes.
        - TokenType.WHITESPACE: Whitespace characters (excluded from the result).
        - TokenType.COMMENT: SQL comments (e.g., -- comment or /* comment */).
        - TokenType.UNKNOWN: Any other unrecognized characters.
    Notes:
        - The function assumes that the `TokenType` enumeration and `Token` class
          are defined elsewhere in the code.
        - The `KEYWORDS` variable should contain a regex pattern for SQL keywords.
    """
    tokens = []

    # Sort by length to match longer keywords first and avoid partial matches
    escaped_functions = sorted(
        [re.escape(func) for func in ALL_SQL_FUNCTIONS], key=len, reverse=True
    )
    escaped_keywords = sorted(
        [re.escape(kw) for kw in SQL_KEYWORDS], key=len, reverse=True
    )

    # Define regex patterns for each TokenType
    token_specification = [
        (TokenType.FUNCTION, r"\b(?:" + "|".join(escaped_functions) + r")\b"),
        (TokenType.KEYWORD, r"\b(?:" + "|".join(escaped_keywords) + r")\b"),
        (TokenType.TABLE, r"(?<=(FROM|JOIN|INTO)\s)\w+"),
        (TokenType.TABLE_ALIAS, r"(?<=(FROM|JOIN|INTO)\s)\w+\s(\w+)"),
        (TokenType.IDENTIFIER, r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
        (TokenType.LITERAL, r"\'[^\']*\'|\"[^\"]*\"|\d+(\.\d+)?"),
        (TokenType.SYMBOL, OP_PATTERN),
        (TokenType.WHITESPACE, r"\s+"),
        (TokenType.UNKNOWN, r"."),
    ]

    # Combine patterns into a single regex
    regex = re.compile(
        "|".join(f"(?P<{tt.name}>{pattern})" for tt, pattern in token_specification),
        re.IGNORECASE,
    )

    # Match tokens in the query
    for match in regex.finditer(query):
        for token_type in TokenType:
            if match.lastgroup == token_type.name:
                value = match.group(token_type.name)
                if token_type != TokenType.WHITESPACE:
                    tokens.append(Token(type=token_type, value=value, space=False))
                break

    return _post_process_tokens(tokens)


def _post_process_tokens(tokens: List[Token]) -> List[Token]:
    table_aliases = set()
    aliases_before_periods = set()

    # First pass: identify all identifiers that precede literal periods
    # This is the key enhancement to quantify table aliases before periods
    for i, token in enumerate(tokens):
        if (
            token.type == TokenType.IDENTIFIER
            and i + 1 < len(tokens)
            and tokens[i + 1].type == TokenType.SYMBOL
            and tokens[i + 1].value == "."
        ):
            aliases_before_periods.add(token.value.lower())

    # Second pass: identify formal table aliases (after FROM/JOIN/INTO keywords)
    for i, token in enumerate(tokens):
        if token.type == TokenType.TABLE and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if (
                next_token.type == TokenType.IDENTIFIER
                and next_token.value.upper() not in SQL_KEYWORDS
                and next_token.value.upper() not in ALL_SQL_FUNCTIONS
            ):
                table_aliases.add(next_token.value.lower())
                tokens[i + 1] = Token(
                    TokenType.TABLE_ALIAS, next_token.value, next_token.space
                )

        # Detect column aliases (after AS keyword)
        elif (
            token.type == TokenType.KEYWORD
            and token.value.upper() == "AS"
            and i + 1 < len(tokens)
        ):
            next_token = tokens[i + 1]
            if (
                next_token.type == TokenType.IDENTIFIER
                and next_token.value.upper() not in SQL_KEYWORDS
                and next_token.value.upper() not in ALL_SQL_FUNCTIONS
            ):
                tokens[i + 1] = Token(
                    TokenType.IDENTIFIER_ALIAS, next_token.value, next_token.space
                )

        # Detect implicit column aliases (identifier after column in SELECT)
        elif token.type == TokenType.IDENTIFIER and i > 0 and i + 1 < len(tokens):
            prev_token = tokens[i - 1]
            next_token = tokens[i + 1]

            # Simple heuristic: if identifier follows another identifier/function and precedes comma/FROM
            if (
                prev_token.type in {TokenType.IDENTIFIER, TokenType.FUNCTION}
                and next_token.value in {",", "FROM"}
                and token.value.upper() not in SQL_KEYWORDS
                and token.value.upper() not in ALL_SQL_FUNCTIONS
            ):
                tokens[i] = Token(TokenType.IDENTIFIER_ALIAS, token.value, token.space)

    # Third pass: identify table alias references with enhanced logic
    # This includes both formally declared aliases and any identifier that precedes a period
    for i, token in enumerate(tokens):
        if (
            token.type == TokenType.IDENTIFIER
            and i + 1 < len(tokens)
            and tokens[i + 1].type == TokenType.SYMBOL
            and tokens[i + 1].value == "."
        ):
            # If it's a formally declared alias OR if it precedes a period, treat as table alias
            if (
                token.value.lower() in table_aliases
                or token.value.lower() in aliases_before_periods
            ):
                tokens[i] = Token(TokenType.TABLE_ALIAS, token.value, token.space)

    return tokens


def preprocess_text(text: str) -> str:
    text = normalize_casing(text)
    text = collapse_extra_spaces(text)
    text = normalize_keyword_casing(text)
    tokens = tokenize_sql(text)
    text = " ".join(token.value for token in tokens)
    return text


def postprocess_text(text: str) -> str:
    text = re.sub(r"\s+\.\s+", ".", text)
    return text

def demonstrate_serialization_workflow():
    """
    Demonstrate the complete workflow: anonymize -> serialize -> optimize -> decode
    """
    print("=== SQL Query Anonymization & Serialization Workflow ===\n")
    
    # Step 1: Original query
    original_query = """
    SELECT c.customer_name, o.order_date, od.quantity * od.price as total
    FROM customers c
    JOIN orders o ON c.id = o.customer_id
    JOIN order_details od ON o.id = od.order_id
    WHERE c.status = 'active' AND o.order_date > '2023-01-01'
    """
    
    print("1. Original Query:")
    print(original_query.strip())
    
    # Step 2: Preprocess and anonymize
    processed_query = preprocess_text(original_query)
    anonymizer = Anonymizer(mapping_file=None)
    
    # Get table alias quantification before anonymization
    alias_info = anonymizer.get_table_aliases_quantification(processed_query)
    print("\n2. Table Aliases Quantification:")
    print(f"   - Aliases found: {alias_info['aliases']}")
    print(f"   - Total alias references: {alias_info['total_references']}")
    
    anonymized_query = anonymizer.anonymize_query(processed_query)
    postprocessed_anonymized = postprocess_text(anonymized_query)
    
    print("\n3. Anonymized Query:")
    print(postprocessed_anonymized)
    
    # Step 3: Serialize for later recall
    serialization_file = "anonymized_query.json"
    anonymizer.serialize_anonymized_query(processed_query, postprocessed_anonymized, serialization_file)
    print(f"\n4. Serialized to: {serialization_file}")
    
    # Step 4: Load serialized data for later recall
    loaded_data = anonymizer.deserialize_and_decode(serialization_file)
    
    print("\n5. Loaded Data Metadata:")
    print(f"   - Timestamp: {loaded_data['metadata'].get('timestamp', 'N/A')}")
    print(f"   - Table Aliases: {loaded_data['table_aliases']}")
    
    # Step 5: Demonstrate decoding capability with the anonymized query
    decoded_original_query = anonymizer.process_optimized_query(postprocessed_anonymized)
    
    print("\n7. Final Decoded Optimized Query:")
    print(decoded_original_query)
    
    print("\n8. Verification - Roundtrip Test:")
    print(f"   Original processed: {processed_query[:50]}...")
    decoded_original = loaded_data['decode_query'](postprocessed_anonymized)
    print(f"   Decoded original:   {decoded_original[:50]}...")
    print(f"   Match: {processed_query.strip() == decoded_original.strip()}")
    
    # Cleanup
    if os.path.exists(serialization_file):
        os.remove(serialization_file)
        print(f"\n9. Cleaned up {serialization_file}")



def main():
    sample_text = [
        # " select name, hire_date  from   customers   where  id =  10 and  name = ' John'  ",
        # "  select * from  orders where   column in (1, 2, 3);",
        # " SELECT p.department as dept  from personnel p where id = 10",
        # "SELECT p.name as Employee FROM personnel p WHERE p.id = 10;",
        # "SELECT p.name, c.id from personnel p JOIN customers c ON p.id = c.person_id WHERE p.age > 30;",
        # "SELECT COUNT(*) as total_orders FROM orders o WHERE order_date >= '2023-01-01';",
    ]

    # Original functionality
    try:
        sql_file_statement = read_sql_file("./data/_raw/messy_sql_1.sql")
        sample_text.append(sql_file_statement)
    except FileNotFoundError:
        print("SQL file not found, skipping file processing")

    for sample in sample_text:
        if sample:  # Only process non-empty samples
            print(f"\nOriginal Text:   {sample}")
            processed_sample = preprocess_text(sample)

            print(f"Processed Text:  {processed_sample}")

            anonymizer = Anonymizer(mapping_file=None)
            anonymized_query = anonymizer.anonymize_query(processed_sample)
            postprocessed_query = postprocess_text(anonymized_query)
            print(f"Anonymized Text: {postprocessed_query}")

    # Run the serialization workflow demonstration
    # demonstrate_serialization_workflow()
    # print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()

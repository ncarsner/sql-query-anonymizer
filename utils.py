import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from constants import ALL_SQL_FUNCTIONS, OP_PATTERN, SQL_KEYWORDS


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

    def __init__(self):
        self.mappings: dict[TokenType, dict[str, str]] = defaultdict(dict)
        self.counters: dict[TokenType, int] = Counter()

    def _prefix(self, token_type: TokenType):
        type_prefixes = {
            TokenType.TABLE: "table",
            TokenType.TABLE_ALIAS: "table_alias",
            TokenType.IDENTIFIER: "identifier",
            # TokenType.IDENTIFIER_ALIAS: "identifier_alias",
            TokenType.LITERAL: "literal",
        }
        if token_type not in type_prefixes:
            raise ValueError(f"Unsupported token type: {token_type}")
        return type_prefixes[token_type]

    def __getitem__(self, identifier: str, token_type: TokenType) -> str:
        print(f"Identifier: {identifier}, Type: {token_type}")

        # Special handling for aliases - return as-is
        if token_type in {TokenType.TABLE_ALIAS}:
            # Check if this alias was already created from a table/identifier
            if token_type == TokenType.TABLE_ALIAS:
                for table_mapping in self.mappings[TokenType.TABLE].values():
                    if identifier.lower() == table_mapping.split("_")[0].lower():
                        return identifier  # Return original alias
            elif token_type == TokenType.IDENTIFIER_ALIAS:
                # Column aliases should always be returned as-is to maintain readability
                return identifier

        m = self.mappings[token_type]
        if identifier in m:
            return m[identifier]

        self.counters[token_type] += 1
        prefix = f"{self._prefix(token_type)}_{self.counters[token_type]}"
        m[identifier] = prefix
        return prefix

    def anonymize(self, query: str) -> str:
        tokens = tokenize_sql(query)

        # Build sets of aliases for reference
        # table_aliases = {token.value.lower() for token in tokens 
        #                 if token.type == TokenType.TABLE_ALIAS}
        # column_aliases = {token.value.lower() for token in tokens 
        #                  if token.type == TokenType.IDENTIFIER_ALIAS}
    
        anonymized_tokens = []
        for i, token in enumerate(tokens):
            if token.type in {TokenType.TABLE, TokenType.IDENTIFIER, TokenType.LITERAL}:
                anonymized_value = self.__getitem__(token.value, token.type)
                anonymized_tokens.append(Token(token.type, anonymized_value, token.space))
            elif token.type in {TokenType.TABLE_ALIAS}:
                # Keep all aliases as-is for readability
                anonymized_tokens.append(token)
            else:
                anonymized_tokens.append(token)

        return " ".join(token.value for token in anonymized_tokens)


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
        - TokenType.IDENTIFIER: Identifiers such as table or column names.
        - TokenType.ALIAS: Aliases for tables or columns.
        - TokenType.LITERAL: String and numeric literals.
        - TokenType.TABLE_ALIAS: Table aliases used in the query.
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
    """Post-process tokens to identify table aliases, column aliases, and qualified identifiers."""
    # processed_tokens = []
    table_aliases = set()

    # First pass: identify table aliases and column aliases
    for i, token in enumerate(tokens):
        # Detect table aliases (after FROM/JOIN)
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
            # Check if we're in SELECT context and this might be an implicit alias
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

    # Second pass: identify table alias references (alias.column pattern)
    for i, token in enumerate(tokens):
        if (
            token.type == TokenType.IDENTIFIER
            and token.value.lower() in table_aliases
            and i + 1 < len(tokens)
            and tokens[i + 1].type == TokenType.SYMBOL
            and tokens[i + 1].value == "."
        ):
            # This is a table alias reference - mark it as TABLE_ALIAS to preserve it
            tokens[i] = Token(TokenType.TABLE_ALIAS, token.value, token.space)

    return tokens


def preprocess_text(text: str) -> str:
    text = normalize_casing(text)
    text = collapse_extra_spaces(text)
    text = normalize_keyword_casing(text)
    tokens = tokenize_sql(text)
    text = " ".join(token.value for token in tokens)
    return text


def anonymize_identifiers(text: str) -> str:
    tokens = tokenize_sql(text)
    anonymized_tokens = []
    identifier_count = 0
    identifier_map = {}

    for token in tokens:
        if token.type == TokenType.IDENTIFIER:
            if token.value not in identifier_map:
                identifier_count += 1
                identifier_map[token.value] = f"identifier_{identifier_count}"
            anonymized_tokens.append(
                Token(
                    type=token.type,
                    value=identifier_map[token.value],
                    space=token.space,
                )
            )
        else:
            anonymized_tokens.append(token)

    return " ".join(token.value for token in anonymized_tokens)


if __name__ == "__main__":
    sample_text = [
        # "  This   is not    a   Sample as tXt.  ",
        # " select name, hire_date  from   customers   where  id =  10 and  name = ' John'  ",
        # "  select * from  orders where   column in (1, 2, 3);",
        # " SELECT p.department as dept  from personnel p where id = 10",
        # "SELECT p.name as Employee FROM personnel p WHERE p.id = 10;",
        "SELECT p.name, c.id from personnel p JOIN customers c ON p.id = c.person_id WHERE p.age > 30;",
        # expected: SELECT alias_1.identifier_1 AS identifier_3 FROM identifier_4 identifier_5 WHERE identifier_4.identifier_6 = 10 ;
    ]
    for sample in sample_text:
        print(f"\nOriginal Text: {sample}")
        processed_sample = preprocess_text(sample)

        print(f"Processed Text: {processed_sample}")
        # print(f"Anonymized Text: {anonymize_identifiers(processed_sample)}")

        anonymizer = Anonymizer()
        anonymized_query = anonymizer.anonymize(processed_sample)
        print(f"w/ Anonymizer Class: {anonymized_query}")

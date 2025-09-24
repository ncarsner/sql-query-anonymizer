import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from constants import ALL_SQL_FUNCTIONS, OP_PATTERN, SQL_KEYWORDS


class TokenType(Enum):
    FUNCTION = auto()
    KEYWORD = auto()
    IDENTIFIER = auto()
    ALIAS = auto()
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

@dataclass
class Anonymizer:
    """A class to anonymize SQL identifiers (table names, column names, literals) in a SQL query
    while preserving SQL keywords and functions.
    Usage:
        anonymizer = Anonymizer()
        anonymized_query = anonymizer.anonymize(sql_query)
    Methods:
        - __init__: Initializes the anonymizer with empty mappings and counters.
        - get: Returns the placeholder for a given identifier, creating a new one if it's not already mapped.
        - anonymize: Takes a SQL query string, tokenizes it, and replaces identifiers with their placeholders.
    """
    def __init__(self):  # set up mappings and counters
        self.table_map = {}
        self.column_map = {}
        self.literal_map = {}
        self.keyword_map = {}
        self.alias_map = {}
        self.table_count = 0
        self.column_count = 0
        self.literal_count = 0
        self.keyword_count = 0
        self.alias_count = 0

    # get() (or `__getitem__` = more Pythonic) → return placeholder for a value, creating one if new
    def __getitem__(self, identifier: str, token_type: TokenType) -> str:
        if token_type == TokenType.IDENTIFIER:
            if identifier not in self.column_map:
                self.column_count += 1
                self.column_map[identifier] = f"identifier_{self.column_count}"
            return self.column_map[identifier]
        elif token_type == TokenType.LITERAL:
            if identifier not in self.literal_map:
                self.literal_count += 1
                self.literal_map[identifier] = f"literal_{self.literal_count}"
            return self.literal_map[identifier]
        elif token_type == TokenType.ALIAS:
            if identifier not in self.alias_map:
                self.alias_count += 1
                self.alias_map[identifier] = f"alias_{self.alias_count}"
            return self.alias_map[identifier]
        # return all other types as is
        elif token_type == TokenType.KEYWORD or token_type == TokenType.FUNCTION:
            return identifier
        elif token_type == TokenType.SYMBOL:
            return identifier
        elif token_type == TokenType.COMMENT:
            return identifier
        elif token_type == TokenType.WHITESPACE:
            return identifier
        return identifier

    """
    def __getitem__(self, identifier: str, token_type: TokenType) -> str:
        # Map token types to their respective maps and counters
        token_map = {
            TokenType.IDENTIFIER: (self.column_map, "identifier_", self.column_count),
            TokenType.LITERAL: (self.literal_map, "literal_", self.literal_count),
            TokenType.ALIAS: (self.table_map, "alias_", self.table_count),
        }

        # Handle token types with maps and counters
        if token_type in token_map:
            token_dict, prefix, count = token_map[token_type]
            if identifier not in token_dict:
                count += 1
                token_dict[identifier] = f"{prefix}{count}"
                # Update the counter back to the object
                if token_type == TokenType.IDENTIFIER:
                    self.column_count = count
                elif token_type == TokenType.LITERAL:
                    self.literal_count = count
                elif token_type == TokenType.ALIAS:
                    self.table_count = count
            return token_dict[identifier]

        # Return identifier directly for other token types
        return identifier
    """

    # anonymize() → loop over tokens, replace TABLE/COLUMN/LITERAL based on clause
    def anonymize(self, query: str) -> str:
        tokens = tokenize_sql(query)
        anonymized_tokens = [
            Token(
                type=token.type,
                value=self.__getitem__(token.value, token.type) if token.type in {TokenType.IDENTIFIER, TokenType.LITERAL, TokenType.ALIAS} else token.value,
                space=token.space
            )
            for token in tokens
        ]
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
        - TokenType.IDENTIFIER: Identifiers such as table or column names.
        - TokenType.ALIAS: Aliases for tables or columns.
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
        (TokenType.IDENTIFIER, r"[a-zA-Z_][a-zA-Z0-9_]*(\.?\w+)?"),
        (TokenType.ALIAS, r"[a-zA-Z_][a-zA-Z0-9_]*\s+(?=\b(?:" + "|".join(escaped_keywords) + r")\b)"),
        (TokenType.LITERAL, r"\'[^\']*\'|\"[^\"]*\"|\d+(\.\d+)?"),
        (TokenType.SYMBOL, OP_PATTERN),
        (TokenType.WHITESPACE, r"\s+"),
        (TokenType.COMMENT, r"--.*?$|/\*.*?\*/"),  # Single line and multi-line comments
        # (TokenType.COMMENT, r"--[^\n]*|/\*[\s\S]*?\*/"),  # newline-agnostic
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
                if (token_type != TokenType.WHITESPACE):
                    tokens.append(Token(type=token_type, value=value, space=False))
                break

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
            anonymized_tokens.append(Token(type=token.type, value=identifier_map[token.value], space=token.space))
        else:
            anonymized_tokens.append(token)

    return " ".join(token.value for token in anonymized_tokens)


if __name__ == "__main__":
    sample_text = [
        "  This   is not    a   Sample as tXt.  ",
        " select name, hire_date  from   customers   where  id =  10 and  name = ' John'  ",
        "  select * from  orders where   column in (1, 2, 3);",
        " SELECT p.department as dept  from personnel p where id = 10",
        "SELECT p.name as Employee FROM personnel p WHERE p.id = 10;",
        # expected: SELECT alias_1.identifier_1 AS identifier_3 FROM identifier_4 identifier_5 WHERE identifier_4.identifier_6 = 10 ;
    ]
    for sample in sample_text:
        print(f"\nOriginal Text: {sample}")
        processed_sample = preprocess_text(sample)

        print(f"Processed Text: {processed_sample}")
        print(f"Anonymized Text: {anonymize_identifiers(processed_sample)}")

        anonymizer = Anonymizer()
        anonymized_query = anonymizer.anonymize(processed_sample)
        print(f"w/ Anonymizer Class: {anonymized_query}")

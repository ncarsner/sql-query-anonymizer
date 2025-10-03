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
    IDENTIFIER = auto()
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
            # TokenType.ALIAS: "alias",
            # TokenType.IDENTIFIER_ALIAS: "identifier_alias",
            # TokenType.TABLE_ALIAS: "table_alias",
            TokenType.IDENTIFIER: "identifier",
            TokenType.LITERAL: "literal",
        }
        if token_type not in type_prefixes:
            raise ValueError(f"Unsupported token type: {token_type}")
        return type_prefixes[token_type]

    def __getitem__(self, identifier: str, token_type: TokenType) -> str:
        print(f"Identifier: {identifier}, Type: {token_type}")
        print("mappings: ", self.mappings)
        print("counters: ", self.counters)

        m = self.mappings[token_type]
        if identifier in m:
            return m[identifier]

        self.counters[token_type] += 1
        prefix = f"{self._prefix(token_type)}_{self.counters[token_type]}"
        m[identifier] = prefix
        return prefix

    def anonymize(self, query: str) -> str:
        tokens = tokenize_sql(query)
        anonymized_tokens = [
            Token(
                type=token.type,
                value=self.__getitem__(token.value, token.type)
                if token.type
                in {
                    TokenType.TABLE,
                    TokenType.IDENTIFIER,
                    TokenType.LITERAL,
                }
                else token.value,
                space=token.space,
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
        (TokenType.TABLE, r"(?<=\bFROM\s)\w+"),
        (TokenType.IDENTIFIER, r"[a-zA-Z_][a-zA-Z0-9_]*(\.?\w+)?"),
        (TokenType.LITERAL, r"\'[^\']*\'|\"[^\"]*\"|\d+(\.\d+)?"),

        # (TokenType.IDENTIFIER_ALIAS, r"(?<=AS\s)\w+"),
        # (TokenType.TABLE_ALIAS, r"(?<=(FROM|JOIN)\s\w+\s)\w+"),

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
        "SELECT p.name as Employee FROM personnel p WHERE p.id = 10;",
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

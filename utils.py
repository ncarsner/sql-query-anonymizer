from enum import Enum, auto
from dataclasses import dataclass
import re
from typing import List


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    SYMBOL = auto()
    LITERAL = auto()
    WHITESPACE = auto()
    UNKNOWN = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    space: bool = False


KEYWORDS = { # fmt: off
    "SELECT", "INSERT", "UPDATE", "DELETE", "DISTINCT", "UNIQUE", "AS", "FROM",
    "JOIN", "INNER JOIN", "OUTER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "FULL OUTER JOIN", "CROSS JOIN",
    "ON", "WHERE", "LIKE", "AND", "OR", "IN", "NOT", "BETWEEN", "IS", "NULL",

    "CASE", "WHEN", "THEN", "ELSE", "END", "UNION", "ALL",

    "GROUP BY", "ORDER BY", "IF", "EXISTS", "ELSEIF", "WITH", "HAVING",
    "LIMIT", "OFFSET",
    "CAST", "COUNT", "SUM", "AVG", "MIN", "MAX", "TRUE", "FALSE", "NULLIF", "COALESCE",
    "ROUND", "LENGTH", "LEN", "SUBSTRING", "SUBSTR", "TRIM", "UPPER", "LOWER",
    "GETDATE", "NOW", "TODAY", "DATEADD", "DATEDIFF", "DATEPART", "CONVERT",

    "CREATE", "ALTER", "DROP", "INDEX", "VIEW", "TRIGGER", "TABLE", "COLUMN",
    "PRIMARY KEY", "FOREIGN KEY", "UNIQUE KEY", "CHECK",
    "DEFAULT", "REFERENCES", "EXCEPT", "INTERSECT", "RECURSIVE",
    
    "INTO", "VALUES",

    "GRANT", "REVOKE",
    "COMMIT", "ROLLBACK", "SAVEPOINT", "TRANSACTION", "LOCK",
    "BEGIN", "END", "DECLARE", "CURSOR", "FETCH", "OPEN", "CLOSE",

    # "TABLESPACE",
    # "ANALYZE",
    # "EXPLAIN",
    # "VACUUM",
    "SET",
    "SHOW",
    "DESCRIBE",
    "USE",
    "RETURNS",
    # "RETURNING",

    "DATABASE", "SCHEMA", "FUNCTION", "PROCEDURE",
    "TRUNCATE", "REPLACE", "MERGE", "UPSERT",
    "ASSERT", "RAISE", "THROW",

    "LOOP", "EXIT", "CONTINUE", "FOR", "WHILE", "DO",

    # "LANGUAGE",
    # "PLPGSQL",
    # "PLSQL",
    # "PLV8",
    # "PLPYTHON",
    # "PLPERLU",
    # "PLTCL",
    # "PLJAVA",
} # fmt: on

SYMBOLS = { # fmt: off
    "*", ",", "(", ")", "[", "]", ";", "_",
    "=", "<=", "<", ">=", ">", "!", "%", "'",
    "+", "-", "/", "^", "&", "|", "~",
} # fmt: on

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
    # return re.sub(r"\s+", " ", text).strip()
    return " ".join(re.split(r"\s+", text.strip()))


def normalize_keyword_casing(text: str) -> str:
    return " ".join(
        word.upper() if word.upper() in KEYWORDS else word for word in text.split()
    )


def tokenize_sql(query: str) -> List[Token]:
    """
    Tokenizes a given SQL query string into a list of tokens.
    This function uses regular expressions to identify and classify different
    components of an SQL query, such as keywords, identifiers, symbols, literals,
    and whitespace. Each identified component is returned as a `Token` object.
    Args:
        query (str): The SQL query string to be tokenized.
    Returns:
        List[Token]: A list of `Token` objects representing the components of the query.
                     Whitespace tokens are excluded from the result.
    Token Types:
        - TokenType.KEYWORD: Whole word SQL keywords (e.g., SELECT, FROM, WHERE).
        - TokenType.IDENTIFIER: Identifiers such as table or column names.
        - TokenType.LITERAL: String and numeric literals.
        - TokenType.SYMBOL: Operators and punctuation outside of quotes.
        - TokenType.WHITESPACE: Whitespace characters (excluded from the result).
        - TokenType.UNKNOWN: Any other unrecognized characters.
    Notes:
        - The function assumes that the `TokenType` enumeration and `Token` class
          are defined elsewhere in the code.
        - The `KEYWORDS` variable should contain a regex pattern for SQL keywords.
    """
    tokens = []
    
    # Define regex patterns for each TokenType
    token_specification = [
        (TokenType.KEYWORD, r'\b(?:' + "|".join(re.escape(kw) for kw in KEYWORDS) + r')\b'),
        (TokenType.IDENTIFIER, r'[a-zA-Z_][a-zA-Z0-9_]*(\.?\w+)?'),
        (TokenType.LITERAL, r'\'[^\']*\'|\"[^\"]*\"|\d+(\.\d+)?'),
        (TokenType.SYMBOL, r'(?<!["\'])(?:' + "|".join(re.escape(sym) for sym in SYMBOLS) + r')(?!["\'])'),
        (TokenType.WHITESPACE, r'\s+'),
        (TokenType.UNKNOWN, r'.'),
    ]
    
    # Combine patterns into a single regex
    token_regex = '|'.join(f'(?P<{tt.name}>{pattern})' for tt, pattern in token_specification)
    regex = re.compile(token_regex, re.IGNORECASE)
    
    # Match tokens in the query
    for match in regex.finditer(query):
        for token_type in TokenType:
            if match.lastgroup == token_type.name:
                value = match.group(token_type.name)
                if token_type != TokenType.WHITESPACE:  # Skip whitespace tokens if not needed
                    tokens.append(Token(type=token_type, value=value, space=False))
                break
    
    return tokens



def preprocess_text(text: str) -> str:
    text = normalize_casing(text)
    text = collapse_extra_spaces(text)
    text = normalize_keyword_casing(text)
    tokens = tokenize_sql(text) # changes to List of Tokens
    text = " ".join(token.value for token in tokens)
    return text


if __name__ == "__main__":
    sample_text = [
        "  This   is not    a   Sample as tXt.  ",
        " select name, hire_date  from   table   where  id =  10 and  name = ' John'  ",
        "  select * from  table where   column in (1, 2, 3);",
        " SELECT p.department as dept  from personnel p where id = 10",
    ]
    for sample in sample_text:
        print(f"\nOriginal Text: '{sample}'")
        print(f"Processed Text: '{preprocess_text(sample)}'")

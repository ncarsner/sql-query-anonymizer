from enum import Enum, auto
from dataclasses import dataclass
import re
from typing import List


class TokenType(Enum):
    FUNCTION = auto()
    KEYWORD = auto()
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

# SQL function sets as constants
SQL_AGGREGATE_FUNCTIONS = {"GROUP_CONCAT", "STRING_AGG", "ARRAY_AGG", "FIRST", "LAST", "BIT_AND", "BIT_OR", "BIT_XOR", "CORR", "COVAR_POP", "COVAR_SAMP", "JSON_AGG", "JSONB_AGG", "XMLAGG", "LISTAGG",}

SQL_STRING_FUNCTIONS = {"UPPER", "LOWER", "SUBSTRING", "SUBSTR", "TRIM", "LENGTH", "LEN", "CONCAT", "REPLACE", "LEFT", "RIGHT", "LPAD", "RPAD", "SPLIT_PART", "CHAR_LENGTH", "CHARINDEX", "POSITION", "INITCAP", "TO_CHAR", "FORMAT", "REGEXP_REPLACE", "REGEXP_MATCHES", "REGEXP_SUBSTR", "TRANSLATE", "STRPOS", "OVERLAY", "BTRIM", "LTRIM", "RTRIM", "ASCII", "CHR", "SOUNDEX", "DIFFERENCE", "CONCAT_WS",}

SQL_DATE_FUNCTIONS = {"NOW", "GETDATE", "DATEADD", "DATEDIFF", "DATEPART", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP", "EXTRACT", "TO_DATE", "TO_TIMESTAMP", "AGE", "TIMESTAMPDIFF", "TIMESTAMPADD", "DAY", "MONTH", "YEAR", "HOUR", "MINUTE", "SECOND", "WEEK", "QUARTER", "TIMEZONE", "TIMEZONE_HOUR", "TIMEZONE_MINUTE", "ISODOW", "ISOWEEK", "JULIANDAY", "STRFTIME", "TO_UNIXTIME", "FROM_UNIXTIME", "SYSDATE", "SYSTIMESTAMP", "LOCALTIMESTAMP", "CURRENT_TIMEZONE", "LOCALTIME",}

SQL_NUMERIC_FUNCTIONS = {"COUNT", "SUM", "AVG", "MIN", "MAX", "ROUND", "CEIL", "FLOOR", "ABS", "POWER", "SQRT", "EXP", "LN", "LOG", "LOG10", "MOD", "RANDOM", "TRUNC", "SIGN", "GREATEST", "LEAST", "DIV", "BIT_LENGTH", "OCTET_LENGTH", "WIDTH_BUCKET", "CUME_DIST", "DENSE_RANK", "PERCENT_RANK", "RANK", "ROW_NUMBER", "NTILE", "CORR", "COVAR_POP", "COVAR_SAMP", "VARIANCE", "STDDEV", "MEDIAN", "MODE",}

ALL_SQL_FUNCTIONS = (SQL_AGGREGATE_FUNCTIONS | SQL_STRING_FUNCTIONS | SQL_DATE_FUNCTIONS | SQL_NUMERIC_FUNCTIONS)

SQL_KEYWORDS = { # fmt: off
    "SELECT", "INSERT", "UPDATE", "DELETE", "DISTINCT", "UNIQUE", "AS", "FROM",
    "JOIN", "INNER JOIN", "OUTER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "FULL OUTER JOIN", "CROSS JOIN",
    "ON", "WHERE", "LIKE", "AND", "OR", "IN", "NOT", "BETWEEN", "IS", "NULL",

    "CASE", "WHEN", "THEN", "ELSE", "END", "UNION", "ALL",

    "GROUP BY", "ORDER BY", "IF", "EXISTS", "ELSEIF", "WITH", "HAVING",
    "LIMIT", "OFFSET",
    "CAST",
    # "COUNT", "SUM", "AVG", "MIN", "MAX",
    "TRUE", "FALSE", "NULLIF", "COALESCE",
    # "ROUND", "LENGTH", "LEN", "SUBSTRING", "SUBSTR", "TRIM", "UPPER", "LOWER",
    # "GETDATE", "NOW", "TODAY", "DATEADD", "DATEDIFF", "DATEPART", "CONVERT",

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
}

SYMBOLS = {
    "*", ",", "()", "(", ")", "[", "]", ";", "_",
    "<=", "<", ">=", ">", "=", "!", "%", "'",
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
    return " ".join(re.split(r"\s+", text.strip()))


def normalize_keyword_casing(text: str) -> str:
    sorted_keywords = sorted(SQL_KEYWORDS | ALL_SQL_FUNCTIONS, key=len, reverse=True)
    pattern = r'\b(?:' + "|".join(map(re.escape, sorted_keywords)) + r')\b'
    return re.sub(pattern, lambda m: m.group(0).upper(), text, flags=re.IGNORECASE)


def tokenize_sql(query: str) -> List[Token]:
    """
    Tokenizes a given SQL query string into a list of tokens, such as keywords, identifiers, symbols, literals,
    and whitespace. Each identified component is returned as a `Token` object.
    Token Types:
        - TokenType.FUNCTION: SQL functions (e.g., COUNT, SUM, UPPER).
        - TokenType.KEYWORD: Whole word SQL keywords (e.g., SELECT, FROM, WHERE).
        - TokenType.IDENTIFIER: Identifiers such as table or column names.
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
    escaped_functions = sorted([re.escape(func) for func in ALL_SQL_FUNCTIONS], key=len, reverse=True)
    escaped_keywords = sorted([re.escape(kw) for kw in SQL_KEYWORDS], key=len, reverse=True)
    
    # Define regex patterns for each TokenType
    token_specification = [
        (TokenType.FUNCTION, r'\b(?:' + "|".join(escaped_functions) + r')\b'),
        (TokenType.KEYWORD, r'\b(?:' + "|".join(escaped_keywords) + r')\b'),
        (TokenType.IDENTIFIER, r'[a-zA-Z_][a-zA-Z0-9_]*(\.?\w+)?'),
        (TokenType.LITERAL, r'\'[^\']*\'|\"[^\"]*\"|\d+(\.\d+)?'),
        (TokenType.SYMBOL, r'(?<![\'"])(?:' + "|".join(re.escape(sym) for sym in SYMBOLS) + r')(?![\'"])'),
        (TokenType.WHITESPACE, r'\s+'),
        (TokenType.COMMENT, r'--[^\n]*|/\*[\s\S]*?\*/'),  # Single line and multi-line comments (newline-agnostic)
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

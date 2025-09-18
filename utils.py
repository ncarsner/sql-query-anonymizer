import re

def normalize_casing(text: str) -> str:
    def ignore_within_quotes(match):
        return match.group(0)

    # Regex to match text outside quotes
    # Explanation of the regex:
    #   (?<!\\)"(?:\\.|[^"\\])*"   : Matches double-quoted strings, ignoring escaped quotes (not preceded by a backslash)
    #   |                         : OR
    #   '.*?'                     : Matches single-quoted strings (non-greedy)
    #   |                         : OR
    #   ([^'"]+)                  : Matches sequences of characters that are not single or double quotes (captures unquoted text)
    pattern = r'(?<!\\)"(?:\\.|[^"\\])*"|\'.*?\'|([^\'"]+)'
    return re.sub(pattern, lambda m: ignore_within_quotes(m) if m.group(0).startswith(("'", '"')) else m.group(0).lower(), text)


def remove_extra_whitespace(text: str) -> str:
    return " ".join(text.split())


def collapse_extra_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_keyword_casing(text: str) -> str:
    keywords = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",

        "DISTINCT",
        "UNIQUE",
        "AS",
        "FROM",
        "JOIN",
        "INNER JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "FULL JOIN",
        "CROSS JOIN",
        "ON",
        "WHERE",

        "AND",
        "OR",
        "IN",
        "NOT",
        "IS",
        "NULL",
        "LIKE",

        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",

        "UNION",
        "ALL",
        "EXISTS",
        "BETWEEN",

        "GROUP BY",
        "ORDER BY",

        "IF",
        "ELSEIF",

        "WITH",
        "HAVING",
        "LIMIT",
        "OFFSET",

        "CAST",
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX",
        "TRUE",
        "FALSE",
        "NULLIF",
        "COALESCE",
        "ROUND",
        "LENGTH",
        "SUBSTRING",
        "TRIM",
        "UPPER",
        "LOWER",

        "CREATE",
        "ALTER",
        "DROP",
        "INDEX",
        "VIEW",
        "TRIGGER",
        "TABLE",

        "PRIMARY KEY",
        "FOREIGN KEY",
        "REFERENCES",

        "EXCEPT",
        "INTERSECT",

        "RECURSIVE",
        "INTO",
        "VALUES",
        # "RETURNING",

        "GRANT",
        "REVOKE",

        "COMMIT",
        "ROLLBACK",
        "SAVEPOINT",
        "TRANSACTION",
        "LOCK",
        # "ANALYZE",
        # "EXPLAIN",
        # "VACUUM",

        "SET",
        "SHOW",
        "DESCRIBE",
        "USE",
        "DATABASE",
        "SCHEMA",
        "FUNCTION",
        "PROCEDURE",
        "DECLARE",
        "CURSOR",
        "FETCH",
        "LOOP",

        "EXIT",
        "CONTINUE",
        "FOR",
        "WHILE",
        "DO",
        "BEGIN",
        "END",

        # "LANGUAGE",
        # "PLPGSQL",
        # "PLSQL",
        # "PLV8",
        # "PLPYTHON",
        # "PLPERLU",
        # "PLTCL",
        # "PLJAVA",
    }
    return " ".join(word.upper() if word.upper() in keywords else word for word in text.split())


def preprocess_text(text: str) -> str:
    """
    Preprocess the input text by normalizing casing and removing extra whitespace.

    Args:
        text (str): The input text to be preprocessed.

    Returns:
        str: The preprocessed text.
    """
    text = normalize_casing(text)
    # text = remove_extra_whitespace(text)
    text = collapse_extra_spaces(text)
    text = normalize_keyword_casing(text)
    return text


def test_preprocess_text():
    assert preprocess_text("  Hello   World!  ") == "hello world!"
    assert preprocess_text("This   is a   Test.") == "this is a test."
    assert preprocess_text("  MULTIPLE    SPACES   ") == "multiple spaces"
    assert preprocess_text("NoExtraSpaces") == "noextraspaces"
    print("All tests passed!")


if __name__ == "__main__":
    sample_text = "  This   is a   Sample TEXT.  "
    sample_text = "select   from   table   where  id =  10 and  name = ' John'  "
    processed_text = preprocess_text(sample_text)
    print(f"Original Text: '{sample_text}'")
    print(f"Processed Text: '{processed_text}'")
    # test_preprocess_text()

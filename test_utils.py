from utils import TokenType, anonymize_identifiers, normalize_casing, collapse_extra_spaces, normalize_keyword_casing, tokenize_sql, preprocess_text, Anonymizer
import pytest

@pytest.mark.parametrize("input_text, expected_output", [
    ("  Hello   World!  ", "  hello   world!  "),
    ("This   is a   Test.", "this   is a   test."),
    ("  MULTIPLE        SPACES   ", "  multiple        spaces   "),
    ("NoExtraSpaces", "noextraspaces"),
    ("  select *    from customers  where 1 = 1;", "  select *    from customers  where 1 = 1;"),
    (" select id  from  orders   where date_field  = ' 4/2/27 ';", " select id  from  orders   where date_field  = ' 4/2/27 ';"),
    ("select * from users where id = 1;", "select * from users where id = 1;"),
    ("select name from employees e where hire_date <= getdate() - 7;", "select name from employees e where hire_date <= getdate() - 7;"),
    ("Insert INTO orders (id, amount) Values (1, 100);", "insert into orders (id, amount) values (1, 100);"),
    ("UPDATE products SET price = 19.99 WHERE id = 2;", "update products set price = 19.99 where id = 2;"),
    ("delete FROM sessions WHERE user_id = 3;", "delete from sessions where user_id = 3;"),
    ("select name, hire_date from employees where id = 10 and name = ' John ';", "select name, hire_date from employees where id = 10 and name = ' John ';")
])
def test_normalize_casing(input_text, expected_output):
    assert normalize_casing(input_text) == expected_output


@pytest.mark.parametrize("input_text, expected_output", [
    ("  Hello   World!  ", "Hello World!"),
    ("This   is a   Test.", "This is a Test."),
    ("  MULTIPLE        SPACES   ", "MULTIPLE SPACES"),
    ("NoExtraSpaces", "NoExtraSpaces"),
    ("Some  S p a c e s  Included ", "Some S p a c e s Included"),
    ("  select *    from customers  where 1 = 1;", "select * from customers where 1 = 1;"),
    (" select id  from  orders   where date_field  = ' 4/2/27 ';", "select id from orders where date_field = ' 4/2/27 ';"),
    (" select name  from  employees e where hire_date <= getdate() - 7;", "select name from employees e where hire_date <= getdate() - 7;"),
])
def test_remove_extra_spaces(input_text, expected_output):
    assert collapse_extra_spaces(input_text) == expected_output


@pytest.mark.parametrize("input_text, expected_output", [
    ("  Hello   World!  ", "  Hello   World!  "),
    ("  select * from cases c where 1 = 1 ;  ", "  SELECT * FROM cases c WHERE 1 = 1 ;  "),
    ("SELECT * FROM users WHERE id = 1;", "SELECT * FROM users WHERE id = 1;"),
    ("Insert INTO orders (id, amount) VALUES (1, 100);", "INSERT INTO orders (id, amount) VALUES (1, 100);"),
    ("UPDATE products SET price = 19.99 WHERE id = 2;", "UPDATE products SET price = 19.99 WHERE id = 2;"),
    ("delete FROM sessions WHERE user_id = 3;", "DELETE FROM sessions WHERE user_id = 3;"),
    ("  select name, hire_date  from   employees   where  id =  10 and  name = ' John'  ", "  SELECT name, hire_date  FROM   employees   WHERE  id =  10 AND  name = ' John'  "),
    (" select name, department from employees e inner join departments d on e.dept_id = d.id where e.hire_date > '2020-01-01' ", " SELECT name, department FROM employees e INNER JOIN departments d ON e.dept_id = d.id WHERE e.hire_date > '2020-01-01' "),
])
def test_normalize_keyword_casing(input_text, expected_output):
    assert normalize_keyword_casing(input_text) == expected_output


@pytest.mark.parametrize("input_text, expected_tokens, expected_types", [
    (
        "SELECT name, hire_date FROM employees e WHERE id = 10 AND name = 'John';",
        ["SELECT", "name", ",", "hire_date", "FROM", "employees", "e", "WHERE", "id", "=", "10", "AND", "name", "=", "'John'", ";"],
        [TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL, TokenType.SYMBOL]
    ),
    (
        "INSERT INTO orders (id, amount) VALUES (1, 100);",
        ["INSERT", "INTO", "orders", "(", "id", ",", "amount", ")", "VALUES", "(", "1", ",", "100", ")", ";"],
        [TokenType.KEYWORD, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.KEYWORD, TokenType.SYMBOL, TokenType.LITERAL, TokenType.SYMBOL, TokenType.LITERAL, TokenType.SYMBOL, TokenType.SYMBOL]
    ),
    (
        "UPDATE products SET price = 19.99 WHERE id = 2;",
        ["UPDATE", "products", "SET", "price", "=", "19.99", "WHERE", "id", "=", "2", ";"],
        [TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL, TokenType.SYMBOL]
    ),
    # (
    #     """-- This is a single line comment
    # SELECT name, hire_date FROM employees e
    # /* multi-line
    # comment */
    # WHERE id = 10 AND name = 'John';
    # """,
    #     ["-- This is a single line comment", "SELECT", "name", ",", "hire_date", "FROM", "employees", "e", "/* multi-line comment */", "WHERE", "id", "=", "10", "AND", "name", "=", "'John'", ";"],
    #     [TokenType.COMMENT, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.IDENTIFIER, TokenType.COMMENT, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL, TokenType.SYMBOL]
    # )
])
def test_tokenize_sql(input_text, expected_tokens, expected_types):
    tokens = tokenize_sql(input_text)
    token_values = [token.value for token in tokens]
    token_types = [token.type for token in tokens]

    assert token_values == expected_tokens
    assert token_types == expected_types


@pytest.mark.parametrize("input_text, expected_output", [
    ("  Hello   World!  ", "hello world !"),
    ("This   is a   Test.", "this IS a test ."),
    ("  MULTIPLE        SPACES   ", "multiple spaces"),
    ("NoExtraSpaces", "noextraspaces"),
    ("  select *    from customers  where 1 = 1;", "SELECT * FROM customers WHERE 1 = 1 ;"),
    (" select id  from  orders   where date_field  = ' 4/2/27 ';", "SELECT id FROM orders WHERE date_field = ' 4/2/27 ' ;"),
    (" select name  from  employees e where hire_date <= getdate() - 7;", "SELECT name FROM employees e WHERE hire_date <= GETDATE ( ) - 7 ;"),
])
def test_preprocess_text(input_text, expected_output):
    assert preprocess_text(input_text) == expected_output


@pytest.mark.parametrize("input_text, expected_output", [
    ("SELECT name, hire_date FROM employees e WHERE id = 10 AND name = 'John';", "SELECT identifier_1 , identifier_2 FROM identifier_3 identifier_4 WHERE identifier_5 = 10 AND identifier_1 = 'John' ;"),
    ("INSERT INTO orders (id, amount) VALUES (1, 100);", "INSERT INTO identifier_1 ( identifier_2 , identifier_3 ) VALUES ( 1 , 100 ) ;"),
    # ("SELECT p.name as Employee FROM personnel p WHERE p.id = 10;", "SELECT alias_1.identifier_1 AS identifier_3 FROM identifier_4 identifier_5 WHERE identifier_4.identifier_6 = 10 ;"),
])
def test_anonymize_identifiers(input_text, expected_output):
    assert anonymize_identifiers(input_text) == expected_output


@pytest.mark.parametrize("query, expected_output, expected_column_count, expected_column_map, expected_literal_count, expected_literal_map", [
    (
        "SELECT name, salary FROM employees WHERE salary > 50000;",
        "SELECT identifier_1 , identifier_2 FROM identifier_3 WHERE identifier_2 > literal_1 ;",
        3,
        {"name": "identifier_1", "salary": "identifier_2", "employees": "identifier_3"},
        1,
        {"50000": "literal_1"}
    )
])
def test_anonymizer_class(query, expected_output, expected_column_count, expected_column_map, expected_literal_count, expected_literal_map):
    a = Anonymizer()

    actual = a.anonymize(query)
    assert actual == expected_output

    assert a.column_count == expected_column_count
    assert a.column_map == expected_column_map
    assert a.literal_count == expected_literal_count
    assert a.literal_map == expected_literal_map
from utils import TokenType, normalize_casing, collapse_extra_spaces, normalize_keyword_casing, tokenize_sql, preprocess_text
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


@pytest.mark.parametrize("query", [
    # "SELECT name, hire_date FROM employees e WHERE id = 10 AND name = 'John';",
    # "INSERT INTO orders (id, amount) VALUES (1, 100);",
])
def test_tokenize_sql(query):
    tokens = tokenize_sql(query)
    token_values = [token.value for token in tokens]
    expected_values = [
        "SELECT", "name", ",", "hire_date", "FROM", "employees", "e",
        "WHERE", "id", "=", "10", "AND", "name", "=", "'John'", ";"
    ]
    assert token_values == expected_values

    # Check token types
    expected_types = [
        TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.IDENTIFIER,
        TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.IDENTIFIER,
        TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL,
        TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.LITERAL,
        TokenType.SYMBOL
    ]
    token_types = [token.type for token in tokens]
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

from utils import collapse_extra_spaces, normalize_casing, preprocess_text
import pytest


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


# @pytest.mark.parametrize("input_text, expected_output", [
#     ("  Hello   World!  ", "hello world!"),
# ])
# def test_normalize_casing(input_text, expected_output):
#     assert normalize_casing(input_text) == expected_output


@pytest.mark.parametrize("input_text, expected_output", [
    # ("  Hello   World!  ", "hello world!"),
    # ("This   is a   Test.", "this IS a test."),
    ("  MULTIPLE        SPACES   ", "multiple spaces"),
    ("NoExtraSpaces", "noextraspaces"),
    ("  select *    from customers  where 1 = 1;", "SELECT * FROM customers WHERE 1 = 1 ;"),
    (" select id  from  orders   where date_field  = ' 4/2/27 ';", "SELECT id FROM orders WHERE date_field = ' 4/2/27 ' ;"),
    (" select name  from  employees e where hire_date <= getdate() - 7;", "SELECT name FROM employees e WHERE hire_date <= GETDATE ( ) - 7 ;"),
])
def test_preprocess_text(input_text, expected_output):
    assert preprocess_text(input_text) == expected_output

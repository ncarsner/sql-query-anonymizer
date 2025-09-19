from utils import preprocess_text
import pytest

@pytest.mark.parametrize("input_text, expected_output", [
    ("  Hello   World!  ", "hello world !"),
    ("This   is a   Test.", "this IS a test ."),
    ("  MULTIPLE    SPACES   ", "multiple spaces"),
    ("NoExtraSpaces", "noextraspaces"),
    ("SELECT p.column from table p where p.id = 10", "SELECT p . column FROM table p WHERE p . id = 10"),
    # (" select id  from  table where column  = ' value ';", "SELECT id FROM table WHERE column =' value ' ;"),
])
def test_preprocess_text(input_text, expected_output):
    assert preprocess_text(input_text) == expected_output

from utils import preprocess_text

def test_preprocess_text():
    assert preprocess_text("  Hello   World!  ") == "hello world!"
    assert preprocess_text("This   is a   Test.") == "this is a test."
    assert preprocess_text("  MULTIPLE    SPACES   ") == "multiple spaces"
    assert preprocess_text("NoExtraSpaces") == "noextraspaces"

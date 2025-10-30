import pytest

from src.sql_query_anonymizer.utils import Anonymizer, TokenType, postprocess_text, preprocess_text


@pytest.fixture
def anonymizer():
    """Fixture to provide a fresh Anonymizer instance for each test."""
    return Anonymizer()


@pytest.fixture
def sample_queries():
    """Fixture providing various SQL queries for testing."""
    return {
        "simple_select": "SELECT name, age FROM users WHERE id = 1",
        "with_joins": "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id",
        "with_aliases": "SELECT u.name as username, p.title as post_title FROM users u JOIN posts p ON u.id = p.user_id",
        "complex_query": """
            SELECT c.customer_name, o.order_date, od.quantity * od.price as total
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            JOIN order_details od ON o.id = od.order_id
            WHERE c.status = 'active' AND o.order_date > '2023-01-01'
        """,
        "with_literals": "SELECT * FROM products WHERE price > 100.50 AND category = 'electronics'",
        "with_functions": "SELECT COUNT(*), AVG(salary) FROM employees WHERE department = 'IT'",
    }


@pytest.fixture
def expected_anonymized():
    """Fixture providing expected anonymized results for validation."""
    return {
        "simple_select": "SELECT identifier_1, identifier_2 FROM table_1 WHERE identifier_3 = literal_1",
        "with_functions": "SELECT COUNT(*), AVG(identifier_1) FROM table_1 WHERE identifier_2 = literal_1",
    }


class TestAnonymize:
    def test_anonymize(self):
        """Main test function - covers basic anonymization functionality."""
        anonymizer = Anonymizer()
        query = "SELECT name, age FROM users WHERE id = 1"
        processed_query = preprocess_text(query)
        anonymized = anonymizer.anonymize(processed_query)

        # Basic checks
        assert "SELECT" in anonymized  # Keywords preserved
        assert "name" not in anonymized  # Identifiers anonymized
        assert "users" not in anonymized  # Table names anonymized
        assert "identifier_" in anonymized  # Anonymized identifiers present
        assert "table_" in anonymized  # Anonymized tables present

    @pytest.mark.parametrize(
        "query_key", ["simple_select", "with_joins", "complex_query", "with_literals"]
    )
    def test_anonymize_different_query_types(
        self, anonymizer, sample_queries, query_key
    ):
        """Parameterized test for different types of SQL queries."""
        query = sample_queries[query_key]
        processed_query = preprocess_text(query)
        anonymized = anonymizer.anonymize(processed_query)

        # Basic assertions that should hold for all queries
        assert len(anonymized) > 0
        assert "SELECT" in anonymized

        # Ensure no original identifiers remain (except aliases)
        original_tokens = processed_query.split()
        anonymized_tokens = anonymized.split()

        # At least some transformation should have occurred
        assert original_tokens != anonymized_tokens


class TestDeanonymize:
    @pytest.mark.parametrize(
        "query_key", ["simple_select", "with_joins", "with_literals", "with_functions"]
    )
    def test_deanonymize_various_queries(self, anonymizer, sample_queries, query_key):
        """Parameterized test for de-anonymization of various query types."""
        original_query = sample_queries[query_key]
        processed_query = preprocess_text(original_query)

        anonymized = anonymizer.anonymize(processed_query)
        deanonymized = anonymizer.de_anonymize(anonymized)

        # Normalize whitespace
        original_normalized = " ".join(processed_query.split())
        deanonymized_normalized = " ".join(deanonymized.split())

        assert original_normalized == deanonymized_normalized


class TestEdgeCases:
    """Test class for edge cases and error conditions."""

    def test_anonymizer_prefix_invalid_token_type(self):
        """Test that _prefix method raises ValueError for unsupported token types."""
        anonymizer = Anonymizer()

        with pytest.raises(ValueError, match="Unsupported token type"):
            anonymizer._prefix(TokenType.KEYWORD)


@pytest.mark.parametrize("query, expected_output",
    [
        (
            "SELECT *, (SELECT COUNT(*) FROM orders o2 WHERE o2.customer_id = c.id) as order_count, (SELECT MAX(total_amount) FROM orders o3 WHERE o3.customer_id = c.id) as max_order FROM customers c WHERE c.status = 'active' AND c.created_date > '2020-01-01' AND c.id IN (SELECT DISTINCT customer_id FROM orders WHERE order_date >= '2023-01-01') AND EXISTS (SELECT 'X' FROM customer_preferences cp WHERE cp.customer_id = c.id AND cp.email_marketing = 'yes') ORDER BY c.last_name, c.first_name LIMIT 1000;",
            "SELECT * , ( SELECT COUNT ( * ) FROM table_1 o2 WHERE o2.identifier_1 = c.identifier_2 ) AS order_count , ( SELECT MAX ( identifier_3 ) FROM table_1 o3 WHERE o3.identifier_1 = c.identifier_2 ) AS max_order FROM table_2 c WHERE c.identifier_4 = literal_1 AND c.identifier_5 > literal_2 AND c.identifier_2 IN ( SELECT DISTINCT identifier_1 FROM table_1 WHERE identifier_6 >= literal_3 ) AND EXISTS ( SELECT literal_4 FROM table_3 cp WHERE cp.identifier_1 = c.identifier_2 AND cp.identifier_7 = literal_5 ) ORDER BY c.identifier_8 , c.identifier_9 LIMIT literal_6 ;",
        )
    ],
)
def test_anonymizer_long_query(query, expected_output):
    processed_sample = preprocess_text(query)
    anonymizer = Anonymizer()
    anonymized_query = anonymizer.anonymize(processed_sample)
    actual = postprocess_text(anonymized_query)

    assert actual == expected_output

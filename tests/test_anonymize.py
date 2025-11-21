import pytest
import json

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
        anonymized = anonymizer.anonymize_query(processed_query)

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
        anonymized = anonymizer.anonymize_query(processed_query)

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

        anonymized = anonymizer.anonymize_query(processed_query)
        deanonymized = anonymizer.de_anonymize_query(anonymized)

        # Normalize whitespace
        original_normalized = " ".join(processed_query.split())
        deanonymized_normalized = " ".join(deanonymized.split())

        assert original_normalized == deanonymized_normalized


class TestSerialization:
    """Test class for serialization and deserialization functionality."""

    def test_serialize_anonymized_query(self, anonymizer, tmp_path):
        """Test serialization of anonymized query with mappings using pickle."""
        original_query = "SELECT c.name FROM customers c WHERE c.id = 1"
        processed_query = preprocess_text(original_query)
        anonymized_query = anonymizer.anonymize_query(processed_query)
        
        # Save mappings using the new pickle-based approach
        serialization_file = tmp_path / "test_serialization.pkl"
        anonymizer.mapping_file = serialization_file
        anonymizer.save()
        
        # Verify file exists
        assert serialization_file.exists()
        
        # Verify we can load and use the mappings
        new_anonymizer = Anonymizer(mapping_file=str(serialization_file))
        new_anonymizer.load()
        
        # Test that loaded anonymizer has the same mappings
        assert len(new_anonymizer.mappings) > 0
        assert len(new_anonymizer.reverse_mappings) > 0
        
        # Verify de-anonymization works with loaded mappings
        decoded = new_anonymizer.de_anonymize_query(anonymized_query)
        assert "name" in decoded.lower() or "customers" in decoded.lower()

    def test_deserialize_and_decode(self, anonymizer, tmp_path):
        """Test deserialization and decoding functionality using pickle."""
        original_query = "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        processed_query = preprocess_text(original_query)
        anonymized_query = anonymizer.anonymize_query(processed_query)
        
        # Save mappings
        serialization_file = tmp_path / "test_deserialize.pkl"
        anonymizer.mapping_file = serialization_file
        anonymizer.save()
        
        # Create new anonymizer and load mappings
        new_anonymizer = Anonymizer(mapping_file=str(serialization_file))
        new_anonymizer.load()
        
        # Test that mappings were loaded
        assert len(new_anonymizer.mappings) > 0
        assert len(new_anonymizer.reverse_mappings) > 0
        
        # Test decoding functionality
        decoded_query = new_anonymizer.de_anonymize_query(anonymized_query)
        original_normalized = " ".join(processed_query.split())
        decoded_normalized = " ".join(decoded_query.split())
        assert original_normalized == decoded_normalized

    def test_process_optimized_query(self, anonymizer):
        original_query = "SELECT name FROM users WHERE active = 1"
        processed_query = preprocess_text(original_query)
        anonymized_query = anonymizer.anonymize_query(processed_query)
        
        # Simulate optimization (add hints)
        optimized_anonymized = anonymized_query.replace("SELECT", "SELECT /*+ INDEX */")
        
        # Process optimized query
        decoded_optimized = anonymizer.process_optimized_query(optimized_anonymized)
        
        # Should contain original identifiers and optimization hints
        assert "name" in decoded_optimized
        assert "users" in decoded_optimized
        assert "INDEX" in decoded_optimized  # The comment content should be there

    def test_table_aliases_quantification(self, anonymizer):
        """Test quantification of table aliases that precede periods."""
        query = "SELECT c.name, c.email, o.total FROM customers c JOIN orders o ON c.id = o.customer_id"
        processed_query = preprocess_text(query)
        
        alias_info = anonymizer.get_table_aliases_quantification(processed_query)
        
        # Should detect aliases 'c' and 'o'
        assert alias_info["aliases_count"] == 2
        assert "c" in alias_info["aliases"]
        assert "o" in alias_info["aliases"]
        assert alias_info["aliases"]["c"] == 3  # c.name, c.email, c.id
        assert alias_info["aliases"]["o"] == 2  # o.total, o.customer_id
        assert alias_info["total_references"] == 5

    def test_serialization_roundtrip_with_optimization(self, anonymizer, tmp_path):
        """Test complete workflow: serialize -> optimize -> decode using pickle."""
        original_query = "SELECT p.name, c.title FROM products p JOIN categories c ON p.category_id = c.id"
        processed_query = preprocess_text(original_query)
        anonymized_query = anonymizer.anonymize_query(processed_query)
        
        # Save mappings
        serialization_file = tmp_path / "roundtrip_test.pkl"
        anonymizer.mapping_file = serialization_file
        anonymizer.save()
        
        # Simulate query optimization
        optimized_anonymized = anonymized_query.replace(
            "SELECT", "SELECT /*+ USE_HASH_JOIN */"
        )
        
        # Load mappings and decode optimized query
        new_anonymizer = Anonymizer(mapping_file=str(serialization_file))
        new_anonymizer.load()
        final_decoded = new_anonymizer.de_anonymize_query(optimized_anonymized)
        
        # Should contain original identifiers and optimization hints
        assert "name" in final_decoded or "products" in final_decoded
        assert "USE_HASH_JOIN" in final_decoded  # The comment content should be there


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
    anonymizer = Anonymizer()  # Don't load persistent mappings for tests
    anonymized_query = anonymizer.anonymize_query(processed_sample)
    actual = postprocess_text(anonymized_query)

    assert actual == expected_output

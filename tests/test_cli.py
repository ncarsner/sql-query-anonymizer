import tempfile
import os
# import json
# from unittest.mock import patch, mock_open

import pytest

from src.sql_query_anonymizer.cli import AnonymizerCLI, create_parser
from src.sql_query_anonymizer.utils import Anonymizer


class TestAnonymizerCLI:

    def test_cli_initialization(self):
        """Test CLI initialization."""
        cli = AnonymizerCLI()
        assert cli.anonymizer is None
        
        # Test setup
        anonymizer = cli.setup_anonymizer()
        assert isinstance(anonymizer, Anonymizer)
        assert cli.anonymizer is not None

    def test_anonymize_query_cli(self):
        cli = AnonymizerCLI()
        query = "SELECT name FROM users WHERE id = 1"
        
        result = cli.anonymize_query(query)
        
        # Should contain anonymized elements
        assert "identifier_" in result
        assert "table_" in result
        assert "literal_" in result
        assert "SELECT" in result  # Keywords preserved

    def test_deanonymize_query_cli(self):
        cli = AnonymizerCLI()
        
        # First anonymize
        original = "SELECT name FROM users WHERE id = 1"
        anonymized = cli.anonymize_query(original)
        
        # Then de-anonymize
        decoded = cli.deanonymize_query(anonymized)
        
        # Key elements should be restored
        assert "name" in decoded.lower()
        assert "users" in decoded.lower()

    def test_process_file_anonymize(self):
        """Test file processing for anonymization."""
        cli = AnonymizerCLI()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as input_file:
            input_file.write("SELECT * FROM products WHERE price > 100")
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            success = cli.process_file(input_path, output_path, "anonymize")
            assert success
            
            # Verify output file was written and contains anonymized content
            with open(output_path, 'r') as f:
                content = f.read()
                assert "table_" in content or "identifier_" in content
            
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_mapping_stats(self):
        """Test mapping statistics display."""
        cli = AnonymizerCLI()
        
        # Create some mappings
        cli.anonymize_query("SELECT name FROM users")
        
        # Test stats (should not raise exception)
        cli.show_mappings()  # This prints to stdout, just test it doesn't crash

    def test_clear_mappings(self):
        """Test clearing mappings."""
        cli = AnonymizerCLI()
        
        # Create mappings
        cli.anonymize_query("SELECT name FROM users")
        anonymizer = cli.setup_anonymizer()
        
        # Verify mappings exist
        assert len(anonymizer.mappings) > 0
        
        # Clear mappings
        cli.clear_mappings()
        
        # Verify mappings are cleared
        total_mappings = sum(len(m) for m in anonymizer.mappings.values())
        assert total_mappings == 0

    def test_export_import_mappings(self, tmp_path):
        """Test exporting and importing mappings."""
        cli = AnonymizerCLI()
        
        # Create some mappings
        cli.anonymize_query("SELECT name, age FROM users WHERE id = 1")
        
        # Export mappings
        export_file = tmp_path / "exported_mappings.json"
        success = cli.export_mappings(str(export_file))
        assert success
        assert export_file.exists()
        
        # Clear mappings
        cli.clear_mappings()
        
        # Import mappings
        success = cli.import_mappings(str(export_file))
        assert success
        
        # Verify mappings were restored
        anonymizer = cli.setup_anonymizer()
        total_mappings = sum(len(m) for m in anonymizer.mappings.values())
        assert total_mappings > 0


class TestArgumentParser:
    """Test class for argument parser functionality."""

    def test_parser_creation(self):
        parser = create_parser()
        assert parser is not None

    def test_anonymize_command_parsing(self):
        parser = create_parser()
        
        # Test with query string
        args = parser.parse_args(["anonymize", "SELECT * FROM users"])
        assert args.command == "anonymize"
        assert args.query == "SELECT * FROM users"

    def test_deanonymize_command_parsing(self):
        parser = create_parser()
        
        args = parser.parse_args(["deanonymize", "SELECT identifier_1 FROM table_1"])
        assert args.command == "deanonymize"
        assert args.query == "SELECT identifier_1 FROM table_1"

    def test_mapping_commands_parsing(self):
        parser = create_parser()
        
        # Test show-mappings
        args = parser.parse_args(["show-mappings"])
        assert args.command == "show-mappings"
        
        # Test clear-mappings
        args = parser.parse_args(["clear-mappings"])
        assert args.command == "clear-mappings"
        
        # Test export-mappings
        args = parser.parse_args(["export-mappings", "backup.json"])
        assert args.command == "export-mappings"
        assert args.path == "backup.json"

    def test_file_options_parsing(self):
        parser = create_parser()
        
        args = parser.parse_args([
            "-m", "custom.json",
            "anonymize", 
            "-f", "input.sql", 
            "-o", "output.sql"
        ])
        
        assert args.command == "anonymize"
        assert args.file == "input.sql"
        assert args.output == "output.sql"
        assert args.mapping_file == "custom.json"

    def test_global_options_parsing(self):
        """Test parsing global options."""
        parser = create_parser()
        
        args = parser.parse_args([
            "--no-auto-save",
            "--verbose",
            "anonymize", 
            "SELECT * FROM users"
        ])
        
        assert args.no_auto_save is True
        assert args.verbose is True


class TestPersistence:
    """Test class for mapping persistence functionality."""

    def test_auto_save_functionality(self, tmp_path):
        """Test auto-save functionality."""
        mapping_file = tmp_path / "auto_save_test.json"
        
        # Create anonymizer with auto-save enabled
        cli = AnonymizerCLI()
        cli.setup_anonymizer(mapping_file=str(mapping_file), auto_save=True)
        
        # Anonymize a query (should trigger auto-save)
        cli.anonymize_query("SELECT name FROM users")
        
        # Mapping file should exist
        assert mapping_file.exists()

    @pytest.mark.skip(reason="Test not implemented yet")
    def test_mapping_file_locations(self):
        """Test different mapping file location strategies."""
        cli = AnonymizerCLI()
        
        # Test default mapping file
        anonymizer = cli.setup_anonymizer()
        default_file = anonymizer.mapping_file
        assert default_file.endswith("mappings.json")
        assert ".sql_anonymizer" in default_file

    def test_persistence_across_sessions(self, tmp_path):
        """Test that mappings persist across different CLI sessions."""
        mapping_file = tmp_path / "session_test.json"
        
        # First session - create mappings
        cli1 = AnonymizerCLI()
        result1 = cli1.anonymize_query(
            "SELECT user_id FROM accounts", 
            mapping_file=str(mapping_file)
        )
        
        # Second session - should load existing mappings
        cli2 = AnonymizerCLI()
        result2 = cli2.anonymize_query(
            "SELECT user_id FROM accounts",  # Same query
            mapping_file=str(mapping_file)
        )
        
        # Results should be identical (same mappings used)
        assert result1 == result2
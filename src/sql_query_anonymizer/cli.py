#!/usr/bin/env python3
"""
SQL Query Anonymizer CLI Tool

This module provides command-line interface functionality for anonymizing SQL queries
while preserving mappings for later de-anonymization.
"""

import argparse
import shutil
import sys
import traceback
from pathlib import Path
from typing import Optional

from .helper_utilities import read_sql_file
from .utils import Anonymizer, postprocess_text, preprocess_text


class AnonymizerCLI:
    """Command-line interface for the SQL Anonymizer."""

    def __init__(self):
        self.anonymizer: Optional[Anonymizer] = None

    def setup_anonymizer(
        self, mapping_file: str | None = None, auto_save: bool = True
    ) -> Anonymizer:
        """Setup and return an Anonymizer instance."""
        if self.anonymizer is None or (
            mapping_file
            and mapping_file != getattr(self.anonymizer, "mapping_file", None)
        ):
            self.anonymizer = Anonymizer(mapping_file=mapping_file)
            if auto_save:
                self.anonymizer.load()  # Load existing mappings if available
        return self.anonymizer

    def anonymize_query(
        self, query: str, mapping_file: str | None = None, auto_save: bool = True
    ) -> str:
        """
        Args:
            query: SQL query to anonymize
            mapping_file: Optional custom mapping file path
            auto_save: Whether to auto-save mappings

        Returns:
            str: Anonymized query
        """
        anonymizer = self.setup_anonymizer(mapping_file, auto_save)
        processed_query = preprocess_text(query)
        anonymized_query = anonymizer.anonymize_query(processed_query)
        if auto_save:
            anonymizer.save()
        return postprocess_text(anonymized_query)

    def deanonymize_query(
        self, query: str, mapping_file: str | None = None, auto_save: bool = True
    ) -> str:
        """
        Args:
            query: Anonymized SQL query to decode
            mapping_file: Optional custom mapping file path
            auto_save: Whether to auto-save mappings

        Returns:
            str: De-anonymized query
        """
        anonymizer = self.setup_anonymizer(mapping_file, auto_save=auto_save)
        result = anonymizer.de_anonymize_query(query)
        if auto_save:
            anonymizer.save()
        return result

    def process_file(
        self,
        input_file: str,
        output_file: str | None = None,
        operation: str = "anonymize",
        mapping_file: str | None = None,
    ) -> bool:
        """
        Process a SQL file for anonymization or de-anonymization.

        Args:
            input_file: Path to input SQL file
            output_file: Path to output file (optional)
            operation: "anonymize" or "deanonymize"
            mapping_file: Optional custom mapping file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read input file
            if input_file.endswith(".sql"):
                query = read_sql_file(input_file)
            else:
                with open(input_file, "r") as f:
                    query = f.read()

            # Process query
            if operation == "anonymize":
                result = self.anonymize_query(query, mapping_file)
            elif operation == "deanonymize":
                result = self.deanonymize_query(query, mapping_file)
            else:
                print(f"Error: Unknown operation '{operation}'")
                return False

            # Write output
            if output_file:
                with open(output_file, "w") as f:
                    f.write(result)
                print(f"Output written to: {output_file}")
            else:
                print("Result:")
                print(result)

            return True

        except Exception as e:
            print(f"Error processing file: {e}")
            return False

    def show_mappings(self, mapping_file: str | None = None) -> None:
        anonymizer = self.setup_anonymizer(mapping_file, auto_save=True)

        print("\n=== Mapping Statistics ===")
        print(f"Mapping file: {anonymizer.mapping_file}")

        total_mappings = sum(len(mappings) for mappings in anonymizer.mappings.values())
        print(f"Total mappings: {total_mappings}")

        if total_mappings > 0:
            print("\nMappings by type:")
            for token_type, mappings in anonymizer.mappings.items():
                if mappings:
                    counter_value = anonymizer.counters.get(token_type, 0)
                    print(
                        f"  {token_type.name}: {len(mappings)} mappings (counter: {counter_value})"
                    )
        else:
            print("No mappings found.")

    def clear_mappings(self, mapping_file: str | None = None) -> None:
        """Clear all mappings."""
        anonymizer = self.setup_anonymizer(mapping_file)
        anonymizer.clear_mappings()
        print("All mappings cleared.")

    def export_mappings(
        self, export_path: str, mapping_file: str | None = None
    ) -> bool:
        """Export mappings to a file."""
        anonymizer = self.setup_anonymizer(mapping_file, auto_save=False)

        try:
            # Save current state to a temporary location
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy the mapping file
            if anonymizer.mapping_file.exists():
                shutil.copy(anonymizer.mapping_file, export_file)
                print(f"Mappings exported to: {export_file}")
                return True
            else:
                # Save current state if file doesn't exist
                temp_file = anonymizer.mapping_file
                anonymizer.mapping_file = export_file
                anonymizer.save()
                anonymizer.mapping_file = temp_file
                print(f"Mappings exported to: {export_file}")
                return True
        except Exception as e:
            print(f"Error exporting mappings: {e}")
            return False

    def import_mappings(
        self, import_path: str, mapping_file: str | None = None
    ) -> bool:
        """Import mappings from a file."""

        try:
            import_file = Path(import_path)
            if not import_file.exists():
                print(f"Error: Import file not found: {import_file}")
                return False

            anonymizer = self.setup_anonymizer(mapping_file)

            # Copy the import file to the mapping location
            shutil.copy(import_file, anonymizer.mapping_file)

            # Reload the mappings
            anonymizer.load()
            print(f"Mappings imported from: {import_file}")
            return True
        except Exception as e:
            print(f"Error importing mappings: {e}")
            return False


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="SQL Query Anonymizer - Anonymize SQL queries while preserving structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Anonymize a query string
  sql-anonymizer anonymize "SELECT name FROM users WHERE id = 1"

  # Anonymize a SQL file
  sql-anonymizer anonymize -f query.sql -o anonymized_query.sql

  # De-anonymize a query
  sql-anonymizer deanonymize "SELECT identifier_1 FROM table_1 WHERE identifier_2 = literal_1"

  # Show current mappings
  sql-anonymizer show-mappings

  # Export mappings to a file
  sql-anonymizer export-mappings backup_mappings.json

  # Use custom mapping file
  sql-anonymizer anonymize -m custom_mappings.json "SELECT * FROM products"
        """,
    )

    # Global options
    parser.add_argument(
        "-m",
        "--mapping-file",
        help="Custom mapping file path (default: ~/.sql_anonymizer/mappings.json)",
    )
    parser.add_argument(
        "--no-auto-save",
        action="store_true",
        help="Disable automatic saving of mappings",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Anonymize command
    anonymize_parser = subparsers.add_parser("anonymize", help="Anonymize SQL query")
    anonymize_parser.add_argument("query", nargs="?", help="SQL query to anonymize")
    anonymize_parser.add_argument("-f", "--file", help="Input SQL file")
    anonymize_parser.add_argument("-o", "--output", help="Output file path")

    # De-anonymize command
    deanonymize_parser = subparsers.add_parser(
        "deanonymize", help="De-anonymize SQL query"
    )
    deanonymize_parser.add_argument(
        "query", nargs="?", help="Anonymized query to decode"
    )
    deanonymize_parser.add_argument(
        "-f", "--file", help="Input file with anonymized query"
    )
    deanonymize_parser.add_argument("-o", "--output", help="Output file path")

    # Mapping management commands
    subparsers.add_parser("show-mappings", help="Show current mapping statistics")
    subparsers.add_parser("clear-mappings", help="Clear all mappings")

    export_parser = subparsers.add_parser(
        "export-mappings", help="Export mappings to file"
    )
    export_parser.add_argument("path", help="Export file path")

    import_parser = subparsers.add_parser(
        "import-mappings", help="Import mappings from file"
    )
    import_parser.add_argument("path", help="Import file path")

    # Interactive mode
    subparsers.add_parser("interactive", help="Start interactive mode")

    return parser


def interactive_mode(cli: AnonymizerCLI) -> None:
    """Run the CLI in interactive mode."""
    print("SQL Anonymizer Interactive Mode")
    print("Type 'help' for available commands, 'quit' to exit")

    while True:
        try:
            command = input("\nsql-anonymizer> ").strip()

            if not command:
                continue

            if command.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if command.lower() == "help":
                print("""
Available commands:
  anonymize <query>     - Anonymize a SQL query
  deanonymize <query>   - De-anonymize a query
  show-mappings         - Show mapping statistics
  clear-mappings        - Clear all mappings
  export <file>         - Export mappings to file
  import <file>         - Import mappings from file
  help                  - Show this help
  quit/exit/q          - Exit interactive mode
                """)
                continue

            # Parse interactive commands
            parts = command.split(None, 1)
            cmd = parts[0].lower()

            if cmd == "anonymize" and len(parts) > 1:
                result = cli.anonymize_query(parts[1])
                print(f"Anonymized: {result}")

            elif cmd == "deanonymize" and len(parts) > 1:
                result = cli.deanonymize_query(parts[1])
                print(f"De-anonymized: {result}")

            elif cmd == "show-mappings":
                cli.show_mappings()

            elif cmd == "clear-mappings":
                cli.clear_mappings()

            elif cmd == "export" and len(parts) > 1:
                cli.export_mappings(parts[1])

            elif cmd == "import" and len(parts) > 1:
                cli.import_mappings(parts[1])

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle no command case
    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = AnonymizerCLI()
    auto_save = not args.no_auto_save

    try:
        if args.command == "anonymize":
            if args.file:
                success = cli.process_file(
                    args.file, args.output, "anonymize", args.mapping_file
                )
                return 0 if success else 1
            elif args.query:
                result = cli.anonymize_query(args.query, args.mapping_file, auto_save)
                if args.output:
                    with open(args.output, "w") as f:
                        f.write(result)
                    print(f"Output written to: {args.output}")
                else:
                    print(result)
                return 0
            else:
                print("Error: Must provide either query string or input file")
                return 1

        elif args.command == "deanonymize":
            if args.file:
                success = cli.process_file(
                    args.file, args.output, "deanonymize", args.mapping_file
                )
                return 0 if success else 1
            elif args.query:
                result = cli.deanonymize_query(args.query, args.mapping_file, auto_save)
                if args.output:
                    with open(args.output, "w") as f:
                        f.write(result)
                    print(f"Output written to: {args.output}")
                else:
                    print(result)
                return 0
            else:
                print("Error: Must provide either query string or input file")
                return 1

        elif args.command == "show-mappings":
            cli.show_mappings(args.mapping_file)
            return 0

        elif args.command == "clear-mappings":
            cli.clear_mappings(args.mapping_file)
            return 0

        elif args.command == "export-mappings":
            success = cli.export_mappings(args.path, args.mapping_file)
            return 0 if success else 1

        elif args.command == "import-mappings":
            success = cli.import_mappings(args.path, args.mapping_file)
            return 0 if success else 1

        elif args.command == "interactive":
            interactive_mode(cli)
            return 0

        else:
            print(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

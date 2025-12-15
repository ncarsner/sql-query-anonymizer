import pickle
import sys
from pathlib import Path

# Adjust sys.path to allow imports when running as a script
sys.path.insert(0, str(Path(__file__).parent.parent))


def read_sql_file(filepath: str) -> str:
    """
    Read a SQL file and return its content, filtering out SQL comments.

    Args:
        filepath: Path to the SQL file

    Returns:
        SQL content as a string with comments removed
    """
    with open(filepath, "r") as f:
        sql_statement = f.read()

    # Ignore lines that start with '--' (SQL comments)
    filtered_lines = [
        line for line in sql_statement.splitlines() if not line.strip().startswith("--")
    ]

    return "\n".join(filtered_lines)


if __name__ == "__main__":
    # Import only when running as a script to avoid circular import
    from .utils import Anonymizer

    # Read the SQL files
    test_query = read_sql_file("./data/_raw/messy_sql_1.sql")
    optimized_query = read_sql_file("./data/_optimized/messy_sql_1o.sql")

    # === Step 1: Anonymize original query and save mappings ===
    print("Step 1: Anonymizing original query...")
    anonymizer = Anonymizer()

    # test_query is already the content, not a filepath
    anonymized = anonymizer.anonymize_query(test_query)
    print(f"Anonymized query: {anonymized[:100]}...")

    # Save the anonymizer state
    with open("anonymizer_mappings.pkl", "wb") as f:
        pickle.dump(anonymizer, f)
    print("Mappings saved to anonymizer_mappings.pkl")

    # === Step 2: Load mappings and deanonymize optimized query ===
    print("\nStep 2: Loading mappings and deanonymizing optimized query...")
    with open("anonymizer_mappings.pkl", "rb") as f:
        loaded_anonymizer = pickle.load(f)

    # optimized_query is already the content, not a filepath
    deanonymized = loaded_anonymizer.de_anonymize_query(optimized_query)

    print("\n=== DEANONYMIZED QUERY ===")
    print(deanonymized)

    # Optionally save to file
    with open("./data/_deanonymized/messy_sql_1_restored.sql", "w") as f:
        f.write(deanonymized)
    print(
        "\nDeanonymized query saved to: ./data/_deanonymized/messy_sql_1_restored.sql"
    )

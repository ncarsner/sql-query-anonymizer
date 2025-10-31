def read_sql_file(filepath: str) -> str:
    with open(filepath, "r") as f:
        sql_statement = f.read()

    # Ignore lines that start with '--' (SQL comments)
    lines = sql_statement.splitlines()
    filtered_lines = []
    for line in lines:
        if line.strip().startswith("--"):
            continue
        filtered_lines.append(line)

    return "".join(filtered_lines).strip().replace("\n", " ")

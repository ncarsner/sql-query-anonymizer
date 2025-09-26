# sql-query-anonymizer
Command-line function to anonymize SQL queries.

## 📌 User Experience
- Receives and validates input
- Normalizes input <i>(casing, spacing, encoding)</i>
- Identifies keywords/namespaces
- Builds reference dictionary <i>(tables, columns, aliases)</i>
- Replaces values
- Validates replaced values
- Renders output w/ reference mapping

---

## 📁 Project Structure

```
sql-query-anonymizer/
│
├── utils/
    ├── constants.py
    └── utils.py
├── main.py
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── README.md
└── LICENSE

```

---

### 📦 Install Requirements

```bash

```

---

## 🔍 Feature Roadmap

### Phase 1: Prototype
- [ ] Passes tests

### Phase 2: Enhancement
- [ ] Support for other dialects

### Phase 3: Deployment
- [ ] Publish on PyPi

### Phase 4: Maintenance & Bug Fixes
- [ ] Submit issues

---

## 🧾 License

MIT

---

## ✍️ Author

Developed by Nicholas Carsner. Contributions welcome!

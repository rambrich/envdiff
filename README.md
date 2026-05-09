# envdiff

> A lightweight CLI tool to diff `.env` files across environments and flag missing or mismatched keys.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/yourname/envdiff.git
cd envdiff && pip install -e .
```

---

## Usage

Compare two `.env` files and see what's missing or mismatched:

```bash
envdiff .env.development .env.production
```

**Example output:**

```
Missing in .env.production:
  - DEBUG
  - STRIPE_TEST_KEY

Mismatched keys:
  - DATABASE_URL  (values differ)

All other keys match.
```

You can also compare multiple files at once:

```bash
envdiff .env.development .env.staging .env.production
```

Use `--keys-only` to ignore values and only check for missing keys:

```bash
envdiff .env.development .env.production --keys-only
```

Use `--output` to write results to a file instead of stdout:

```bash
envdiff .env.development .env.production --output report.txt
```

---

## Options

| Flag | Description |
|------|-------------|
| `--keys-only` | Only check for missing keys, ignore value differences |
| `--quiet` | Suppress output, exit with non-zero code if differences found |
| `--output <file>` | Write diff results to a file instead of stdout |
| `--version` | Show the current version |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | No differences found |
| `1` | Differences detected |
| `2` | Error (e.g. file not found, invalid format) |

---

## License

This project is licensed under the [MIT License](LICENSE).

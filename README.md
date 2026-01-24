# QA Xray Utility

A small Python utility to help QA teams integrate test results and test case data with Xray (for Jira). This README provides installation instructions, configuration details, usage examples, and guidance for contributing.

## Features

- Import test execution results (JUnit, TestNG, Cucumber, etc.) into Xray.
- Export or synchronize test cases between a local repository and Xray.
- Create or update test executions and map results to Xray test cases.
- Support for environment-based configuration and secure API tokens.

## Requirements

- Python 3.8+
- Requests (or an HTTP client of your choice)
- (Optional) Libraries to parse test report formats you use (e.g., junitparser, behave, pytest-xdist adapters)

Install using pip (see installation section).

## Installation

Recommended: create a virtual environment and install from source.

1. Clone the repository:

   git clone https://github.com/Jaipal501caet/qa-xray-utility.git
   cd qa-xray-utility

2. Create and activate a virtual environment:

   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .\.venv\Scripts\activate  # Windows

3. Install dependencies:

   pip install -r requirements.txt

Or, if you publish this package to PyPI later, install with:

   pip install qa-xray-utility

## Configuration

This utility communicates with Xray/Jira using API credentials and a base URL. You can provide configuration via environment variables or a config file.

Recommended environment variables:

- XRAY_BASE_URL - Base URL for Jira/Xray API (e.g. https://your-domain.atlassian.net)
- XRAY_API_TOKEN - API token (or Xray-specific token) with the required scopes
- XRAY_USER_EMAIL - (Optional) Jira user email if using basic auth with API token
- XRAY_PROJECT_KEY - Default project key to use when creating/updating tests/executions

Example (.env):

XRAY_BASE_URL=https://your-domain.atlassian.net
XRAY_API_TOKEN=your_api_token_here
XRAY_USER_EMAIL=you@example.com
XRAY_PROJECT_KEY=PROJ

Note: Avoid committing credentials to source control. Use secrets in CI/CD or environment variables in deployment.

## Usage

This README provides generic usage examples. Replace command names and options with the actual ones implemented in the repository if they differ.

CLI examples (replace with actual commands implemented by the utility):

- Import test results into Xray:

  python -m qa_xray_utility import-results --file path/to/results.xml --format junit --project PROJ

- Create a test execution and upload results:

  python -m qa_xray_utility create-execution --name "Daily CI Run" --file results.xml --project PROJ

- Export test cases from Xray to local JSON/YAML:

  python -m qa_xray_utility export-tests --project PROJ --output tests.json

- Sync local test case files with Xray:

  python -m qa_xray_utility sync-tests --dir ./tests/ --project PROJ --dry-run

Python API example (if the package exposes functions):

from qa_xray_utility.client import XrayClient

client = XrayClient(base_url=os.getenv('XRAY_BASE_URL'), api_token=os.getenv('XRAY_API_TOKEN'))
client.import_results('PROJ', 'path/to/results.xml')

Replace the above with the actual module and class names available in the repository.

## Logging & Troubleshooting

- Enable verbose logging via an environment variable or CLI flag (e.g., --verbose) to see HTTP requests and responses.
- Inspect error messages returned from the API; common issues include authentication errors, missing scopes, or incorrect project keys.
- If uploads fail for large files, check API size limits and consider splitting large reports.

## CI/CD Integration

- Store XRAY_API_TOKEN securely in your CI environment (GitHub Actions Secrets, GitLab CI variables, etc.).
- Add a job to run tests, generate the test report, then call the utility to upload results to Xray.

Example (GitHub Actions snippet):

jobs:
  upload-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m venv .venv
          . .venv/bin/activate
          pip install -r requirements.txt
      - name: Run tests
        run: pytest --junitxml=results.xml
      - name: Upload results to Xray
        env:
          XRAY_BASE_URL: ${{ secrets.XRAY_BASE_URL }}
          XRAY_API_TOKEN: ${{ secrets.XRAY_API_TOKEN }}
          XRAY_USER_EMAIL: ${{ secrets.XRAY_USER_EMAIL }}
        run: |
          python -m qa_xray_utility import-results --file results.xml --format junit --project ${{ secrets.XRAY_PROJECT_KEY }}

## Tests

If the repository contains tests, run them with:

  pytest

Add or update tests to cover parsing/report uploading flows and error handling.

## Contributing

Contributions are welcome. Please:

1. Open an issue to discuss large changes.
2. Fork the repo and create a feature branch.
3. Submit a pull request with tests and documentation updates.

Follow the project's code style and linting rules.

## Roadmap / TODO

- Add native support for more report formats (e.g., NUnit, XUnit, Cucumber JSON).
- Add automated mapping between test IDs and Xray test keys.
- Implement parallel uploads and retry/backoff logic for large suites.

## License

Specify your license here (e.g., MIT). If you don't have a LICENSE file yet, add one to the repository.

## Contact

If you need help or want to report bugs, open an issue on this repository or contact the maintainer.

---

Note: I created a general README template tailored for a QA -> Xray integration utility. If you want, I can:

- Update the README to match the repository's actual CLI commands and module names (point me to the main script or package entrypoint).
- Add badges (build, PyPI) and examples using real endpoints from your codebase.

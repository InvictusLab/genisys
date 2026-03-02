# genisys

![PyPI version](https://img.shields.io/pypi/v/genisys.svg)

Designed for continuous self-learning and iterative improvement, enabling autonomous evolution through adaptive feedback and knowledge refinement.

* Created by **[Krystal](www.invictuslab.cn)**
  * GitHub: https://github.com/InvictusLab
  * PyPI: https://pypi.org/user/invictuslab001/
* PyPI package: https://pypi.org/project/genisys/
* Free software: MIT License

## Features

* TODO

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to GitHub Pages.

* **Live site:** https://InvictusLab.github.io/genisys/
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via GitHub Actions. To enable this, go to your repo's Settings > Pages and set the source to **GitHub Actions**.

## Development

To set up for local development:

```bash
# Clone your fork
git clone git@github.com:your_username/genisys.git
cd genisys

# Install in editable mode with live updates
uv tool install --editable .
```

This installs the CLI globally but with live updates - any changes you make to the source code are immediately available when you run `genisys`.

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
just qa
```

## Author

genisys was created in 2026 by Krystal.

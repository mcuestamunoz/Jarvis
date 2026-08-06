"""CLI entry shim: ``python -m jarvis.main --chat``.

Delegates to ``jarvis.adapters.cli.main`` so documented and actual entrypoints match.
"""
from jarvis.adapters.cli.main import main

if __name__ == "__main__":
    main()

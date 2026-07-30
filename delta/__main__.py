# delta/__main__.py
"""
Delta - Entry point for `python -m delta`.
"""
import sys
from delta.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Delta interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        sys.exit(1)
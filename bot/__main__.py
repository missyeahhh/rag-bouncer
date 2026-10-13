"""python -m bot ask "your question" """
import json
import sys

from .answer import ask

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "ask":
        sys.exit('usage: python -m bot ask "your question"')
    print(json.dumps(ask(" ".join(sys.argv[2:])), indent=2))

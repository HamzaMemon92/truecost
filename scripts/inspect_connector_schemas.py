import sys
import os
import inspect
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.api.endpoints.aggregator import connectors

for name, conn in sorted(connectors.items()):
    source = inspect.getsource(conn.parse_search_results)
    lines = source.strip().split('\n')[:15]
    print(f"=== {name} ({conn.__class__.__name__}) ===")
    print('\n'.join(lines))
    print()

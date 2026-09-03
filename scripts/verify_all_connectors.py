import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.api.endpoints.aggregator import connectors

print(f"Total registered connectors: {len(connectors)}")
for name, conn in sorted(connectors.items()):
    print(f"  {name}: {conn.__class__.__name__} (provider_name='{getattr(conn, 'provider_name', 'N/A')}')")

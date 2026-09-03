import re
content = "const mockRoute = { params: { provider: 'zepto', query: 'Oreo Vanilla Creme Biscuit 120 g', caseId: 'common_oreo', domain: 'grocery', runId: 'zepto_common_oreo' } };"
new_route = "REPLACED"
print(re.sub(r"const mockRoute = \{ params: \{ provider: .*? \} \};", new_route, content))

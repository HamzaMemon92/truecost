from typing import Any

class InMemorySearchCache:
    def __init__(self):
        self.cache: dict[str, dict[str, list[dict[str, Any]]]] = {}
        
    def store(self, category: str, query: str, products: list[dict[str, Any]]):
        cat = str(category).lower().strip()
        q = str(query).lower().strip()
        if cat not in self.cache:
            self.cache[cat] = {}
        if q not in self.cache[cat]:
            self.cache[cat][q] = []
        self.cache[cat][q].extend(products)
        
    def search(self, category: str, query: str) -> list[dict[str, Any]]:
        cat = str(category).lower().strip()
        q = str(query).lower().strip()
        
        if cat not in self.cache:
            return []
            
        results = []
        query_words = set(q.split())
        if not query_words:
            return []
            
        for stored_query, products in self.cache[cat].items():
            stored_words = set(stored_query.split())
            if query_words.issubset(stored_words) or stored_words.issubset(query_words):
                results.extend(products)
                
        seen = []
        unique_results = []
        for p in results:
            pid = p.get("id") or str(p)
            if pid not in seen:
                seen.append(pid)
                unique_results.append(p)
                
        return unique_results

search_cache = InMemorySearchCache()

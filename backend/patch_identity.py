import re

with open('app/services/product_identity.py', 'r') as f:
    content = f.read()

aliases = '''
_NAME_ALIASES = {
    "mobility": {
        "ubergo": "economy",
        "ola mini": "economy",
        "rapido auto": "auto",
        "bike taxi": "bike",
    },
    "pharmacy": {
        "paracetamol": "acetaminophen",
        "crocin": "paracetamol",
        "dolo": "paracetamol",
    },
    "food": {
        "paneer makhani": "paneer butter masala",
        "dal fry": "dal tadka",
    },
    "travel": {
        "delhi": "DEL",
        "mumbai": "BOM",
    }
}
'''
content = content.replace('_CATEGORY_ALIASES = {', aliases + '\n_CATEGORY_ALIASES = {')

# Let's see if we can just do the replacement in _selected_factors since we need category
content = content.replace(
    '        tokens = self._tokens(f"{brand} {name} {structured_size}")',
    '''        # Apply aliases
        alias_dict = _NAME_ALIASES.get(self._category_key(category), {})
        n = name.casefold()
        for k, v in alias_dict.items():
            if k in n:
                if self._category_key(category) == 'travel' and k in ('delhi', 'mumbai'):
                    name = re.sub(rf"\\b{k}\\b", v, name, flags=re.I)
                else:
                    name = re.sub(rf"\\b{k}\\b", v, name, flags=re.I)
        # Normalize travel IATA
        if self._category_key(category) == 'travel':
            name = name.upper()
        
        tokens = self._tokens(f"{brand} {name} {structured_size}")'''
)

with open('app/services/product_identity.py', 'w') as f:
    f.write(content)

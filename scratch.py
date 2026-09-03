import sys
sys.path.append('backend')
from app.services.entity_resolution import entity_resolution_service

name = 'Amul Taaza Homogenised Toned Milk'
resolution = entity_resolution_service.resolve(
    query=name,
    selected_product={'name': name},
    category='Grocery',
    source_record=__import__('app.services.entity_resolution', fromlist=['SourceRecord']).SourceRecord(
        provider='bigbasket',
        product=__import__('app.schemas.product', fromlist=['TrueCostProduct']).TrueCostProduct(
            id='test',
            name='Taaza Homogenised Toned Milk',
            brand='Amul',
            category='Dairy',
            prices=[{'provider':'bigbasket','price':60}]
        )
    )
)
print('Decision:', resolution.decision)
print('Evidence:', resolution.evidence)

import json, os, sys

def test_amazon():
    from app.connectors.amazon import AmazonConnector
    payload = {
        'amazonData': [
            {'name': 'Adilqadri Oudh Al Hashmi Attar 20ml', 'price': 299, 'image': 'https://m.media-amazon.com/images/I/51aBcDef.jpg', 'url': 'https://www.amazon.in/dp/B09XYZ123'},
            {'name': 'Adilqadri White Oudh Attar 10ml', 'price': 199, 'image': 'https://m.media-amazon.com/images/I/51GhIjkL.jpg', 'url': 'https://www.amazon.in/dp/B09XYZ456'},
            {'name': 'No price product', 'price': 0},
        ]
    }
    c = AmazonConnector()
    r = c.parse_search_results(payload)
    issues = []
    if len(r) != 2:
        issues.append(f"Expected 2 products (1 skipped for no price), got {len(r)}")
    for p in r:
        if not p.name: issues.append("Product has no name")
        if p.prices[0].price <= 0: issues.append(f"Zero price for {p.name}")
        if not p.prices[0].deep_link.startswith("https://"): issues.append(f"Bad URL for {p.name}")
        if p.id == "": issues.append("Empty id")
    return r, issues

def test_flipkart():
    from app.connectors.flipkart import FlipkartConnector
    c = FlipkartConnector()
    if os.path.exists('debug_flipkart.json'):
        with open('debug_flipkart.json', encoding='utf-8') as f:
            payload = json.load(f)
        r = c.parse_search_results(payload)
        if len(r) > 0:
            return r, []
    # synthetic
    payload = {'multiWidgetState': {'widgetsData': {'slots': [{'slotData': {'widget': {
        'type': 'PRODUCT_SUMMARY_V2',
        'data': {'products': [
            {
                'action': {'url': '/jbl-tune-520bt/p/itm1234?pid=AUDPID123'},
                'value': {
                    'titles': {'title': 'JBL Tune 520BT Bluetooth Headset', 'superTitle': 'JBL', 'newTitle': 'JBL Tune 520BT'},
                    'pricing': {'displayPrice': 1999, 'strikeOffPrice': 3999},
                    'images': [{'imageUrl': 'https://rukminim1.flixcart.com/image/{@width}/{@height}/xif0q/test.jpg?q={@quality}&crop=false'}],
                    'productMeta': {'productId': 'AUDPID123'}
                }
            }
        ]}
    }}}]}}}
    r = c.parse_search_results(payload)
    issues = []
    if len(r) == 0: issues.append("No products parsed from synthetic payload")
    for p in r:
        if not p.name: issues.append("Product has no name")
        if p.prices[0].price <= 0: issues.append(f"Zero price for {p.name}")
        if not p.prices[0].deep_link.startswith("https://"): issues.append(f"Bad URL for {p.name}: {p.prices[0].deep_link}")
        if p.image_url and '{@width}' in p.image_url: issues.append(f"Image URL template not replaced: {p.image_url}")
    return r, issues

def test_meesho():
    from app.connectors.meesho import MeeshoConnector
    payload = {
        'products': [
            {'productName': 'Adilqadri Attar Roll-On 5.5ml', 'discountedPrice': 149, 'mrp': 299, 'images': ['https://images.meesho.com/images/test.jpg'], 'id': 12345, 'slug': 'adilqadri-attar-12345'},
            {'productName': 'White Oudh Perfume 10ml', 'discountedPrice': 99, 'mrp': 199, 'images': [{'src': 'https://images.meesho.com/images/test2.jpg'}], 'id': 67890, 'slug': 'white-oudh-67890'},
            {'productName': 'No price product', 'discountedPrice': 0},
        ]
    }
    c = MeeshoConnector()
    r = c.parse_search_results(payload)
    issues = []
    if len(r) != 2: issues.append(f"Expected 2 products, got {len(r)}")
    for p in r:
        if not p.name: issues.append("Product has no name")
        if p.prices[0].price <= 0: issues.append(f"Zero price for {p.name}")
        if not p.prices[0].deep_link.startswith("https://"): issues.append(f"Bad URL: {p.prices[0].deep_link}")
        # Check MRP is set when mrp > price
        first = [x for x in [{'productName': 'Adilqadri Attar Roll-On 5.5ml', 'discountedPrice': 149, 'mrp': 299}] if x['productName'] in p.name]
        if first and p.prices[0].original_price != 299:
            issues.append(f"Expected original_price=299, got {p.prices[0].original_price}")
    return r, issues

def test_myntra():
    from app.connectors.myntra import MyntraConnector
    payload = {
        'products': [
            {'productName': 'Adilqadri Black Musk Perfume', 'brandName': 'Adilqadri', 'price': {'discounted': 799, 'mrp': 1299}, 'landingPageUrl': '/adilqadri-black-musk-800024849/buy', 'images': [{'src': 'https://assets.myntassets.com/test.jpg'}]},
            {'productName': 'Skinn Celeste EDT 100ml', 'brandName': 'Skinn', 'price': {'discounted': 1200, 'mrp': 2000}, 'landingPageUrl': '/skinn-celeste-123456/buy', 'images': [{'src': 'https://assets.myntassets.com/test2.jpg'}]},
            {'productName': 'No price product', 'brandName': 'X', 'price': {'discounted': 0, 'mrp': 0}},
        ]
    }
    c = MyntraConnector()
    r = c.parse_search_results(payload)
    issues = []
    if len(r) != 2: issues.append(f"Expected 2 products (1 zero-price skipped), got {len(r)}")
    for p in r:
        if not p.name: issues.append("Product has no name")
        if p.prices[0].price <= 0: issues.append(f"Zero price for {p.name}")
        if not p.prices[0].deep_link.startswith("https://"): issues.append(f"Bad URL: {p.prices[0].deep_link}")
    return r, issues

tests = [
    ("AMAZON", test_amazon),
    ("FLIPKART", test_flipkart),
    ("MEESHO", test_meesho),
    ("MYNTRA", test_myntra),
]

all_passed = True
for name, fn in tests:
    try:
        r, issues = fn()
        if issues:
            print(f"[FAIL] {name}: {len(r)} products, ISSUES: {issues}")
            all_passed = False
        else:
            print(f"[PASS] {name}: {len(r)} products parsed correctly")
            for p in r[:2]:
                print(f"       - {p.name[:55]} | Rs.{p.prices[0].price} | mrp:{p.prices[0].original_price} | img:{bool(p.image_url)}")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        import traceback; traceback.print_exc()
        all_passed = False

print()
if all_passed:
    print("ALL 4 PROVIDER CONNECTORS: 100% PASS")
else:
    print("SOME TESTS FAILED - see above")
    sys.exit(1)

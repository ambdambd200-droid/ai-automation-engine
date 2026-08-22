from selector_cache import get_selector_cache
cache = get_selector_cache()
cache.add_selectors('nafezly', 'card', ['.project-box', '.main-nafez-box-styles'], 'manual')
cache.add_selectors('nafezly', 'title', ['a[href]', '.text-truncate a', 'h4 a'], 'manual')
cache.add_selectors('nafezly', 'link', ['a[href]'], 'manual')
cache.add_selectors('nafezly', 'budget', ['.price', '.budget', '.amount', '[class*="price"]'], 'manual')
print('Added selectors for nafezly')
print('Card:', cache.get_selectors('nafezly', 'card'))
print('Title:', cache.get_selectors('nafezly', 'title'))
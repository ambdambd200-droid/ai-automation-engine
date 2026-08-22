from selector_cache import get_selector_cache
cache = get_selector_cache()
cache.add_selectors('mostaql', 'card', ['.project-row', '.collection-browse--table', 'table.projects-table'], 'manual')
cache.add_selectors('mostaql', 'title', ['.card--title a', 'h3 a', '.project__title a', 'a[href*="/project/"]'], 'manual')
cache.add_selectors('mostaql', 'link', ['.card--title a', 'h3 a', 'a[href*="/project/"]'], 'manual')
cache.add_selectors('mostaql', 'budget', ['.project__meta .budget', '.price', '[class*="price"]', '.amount'], 'manual')
print('Added selectors for mostaql')
print('Card:', cache.get_selectors('mostaql', 'card'))
print('Title:', cache.get_selectors('mostaql', 'title'))
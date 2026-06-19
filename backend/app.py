from flask import Flask, render_template, request, jsonify
import meilisearch
import os

app = Flask(__name__)

MEILI_HOST = os.environ.get("MEILI_HOST", "http://localhost:7700")
MEILI_MASTER_KEY = os.environ.get("MEILI_MASTER_KEY", "masterKeyToChange123")

try:
    meili_client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
except Exception as e:
    print(f"Could not connect to Meilisearch: {e}")
    meili_client = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/how-it-works')
def how_it_works():
    return render_template('how-it-works.html')

@app.route('/indexing-policy')
def indexing_policy():
    return render_template('indexing-policy.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    sort_param = request.args.get('sort', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    in_stock = request.args.get('in_stock', 'false').lower() == 'true'
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 24))
    offset = (page - 1) * limit
    
    # Dynamic facets
    category_param = request.args.get('category', '')
    brand_param = request.args.get('brand', '')
    ram_param = request.args.get('ram', '')
    storage_param = request.args.get('storage', '')
    source_site_param = request.args.get('source_site', '')
    
    if not meili_client:
        return jsonify({"error": "Search engine not available"}), 500
        
    try:
        search_params = {
            'limit': limit,
            'offset': offset,
            'facets': ['category', 'brand', 'ram', 'storage', 'price_numeric', 'source_site']
        }
        
        filter_conditions = []
                
        # Helper to apply facet filters
        def add_facet_filter(field, param_val):
            if param_val:
                f_filter = " OR ".join([f"{field} = '{v.strip()}'" for v in param_val.split(',') if v.strip()])
                if f_filter:
                    filter_conditions.append(f"({f_filter})")
                    
        add_facet_filter('category', category_param)
        add_facet_filter('brand', brand_param)
        add_facet_filter('ram', ram_param)
        add_facet_filter('storage', storage_param)
        add_facet_filter('source_site', source_site_param)
            
        if min_price and min_price.isdigit():
            filter_conditions.append(f"price_numeric >= {min_price}")
            
        if max_price and max_price.isdigit():
            filter_conditions.append(f"price_numeric <= {max_price}")
            
        if in_stock:
            filter_conditions.append("stock_status = 'In Stock'")
            
        if filter_conditions:
            search_params['filter'] = filter_conditions
            
        if sort_param:
            search_params['sort'] = [sort_param]
            
        results = meili_client.index('items').search(query, search_params)
        
        return jsonify({
            'hits': results['hits'],
            'totalHits': results.get('estimatedTotalHits', 0),
            'page': page,
            'limit': limit,
            'facetDistribution': results.get('facetDistribution', {}),
            'facetStats': results.get('facetStats', {})
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
import meilisearch
import psycopg2
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

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
    source_param = request.args.get('source', '')
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
    
    if not meili_client:
        return jsonify({"error": "Search engine not available"}), 500
        
    try:
        search_params = {
            'limit': limit,
            'offset': offset,
            'facets': ['category', 'brand', 'ram', 'storage', 'price_numeric', 'source_site']
        }
        
        filter_conditions = []
        source_site_param = request.args.get('source_site', '')
        if source_site_param:
            sources_filter = " OR ".join([f"source_site = '{s.strip()}'" for s in source_site_param.split(',') if s.strip()])
            if sources_filter:
                filter_conditions.append(f"({sources_filter})")
                
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

def get_db_connection():
    db_settings = {
        "dbname": os.environ.get("POSTGRES_DB", "lanka_aggregator"),
        "user": os.environ.get("POSTGRES_USER", "scraper_user"),
        "password": os.environ.get("POSTGRES_PASSWORD", "supersecret"),
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
    }
    return psycopg2.connect(**db_settings)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_config (
                key VARCHAR(255) PRIMARY KEY,
                value VARCHAR(255) NOT NULL
            );
        ''')
        cursor.execute("SELECT value FROM admin_config WHERE key = 'admin_password_hash';")
        row = cursor.fetchone()
        
        if not row:
            default_pass = os.environ.get('ADMIN_PASS', 'admin')
            pass_hash = generate_password_hash(default_pass)
            cursor.execute(
                "INSERT INTO admin_config (key, value) VALUES (%s, %s);",
                ('admin_password_hash', pass_hash)
            )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB init error: {e}")

# Initialize db config table on startup
init_db()

def check_auth(username, password):
    admin_user = os.environ.get('ADMIN_USER', 'admin')
    if username != admin_user:
        return False
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM admin_config WHERE key = 'admin_password_hash';")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return check_password_hash(row[0], password)
    except Exception:
        pass
        
    return password == os.environ.get('ADMIN_PASS', 'admin')

def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@requires_auth
def admin_dashboard():
    stats = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT source_site, COUNT(id) as item_count, MAX(scraped_at) as last_scraped
            FROM raw_items
            GROUP BY source_site
            ORDER BY item_count DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            stats.append({
                "source_site": row[0],
                "item_count": row[1],
                "last_scraped": row[2]
            })
        cursor.close()
        conn.close()
    except Exception as e:
        error = str(e)
        
    return render_template('admin.html', stats=stats, error=error)

@app.route('/admin/change-password', methods=['POST'])
@requires_auth
def change_password():
    current_pass = request.form.get('current_password')
    new_pass = request.form.get('new_password')
    
    auth = request.authorization
    if not auth or not check_auth(auth.username, current_pass):
        return jsonify({"error": "Incorrect current password."}), 403
        
    if not new_pass or len(new_pass) < 4:
        return jsonify({"error": "New password must be at least 4 characters long."}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        new_hash = generate_password_hash(new_pass)
        cursor.execute(
            "UPDATE admin_config SET value = %s WHERE key = 'admin_password_hash';",
            (new_hash,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

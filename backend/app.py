from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
import meilisearch
import psycopg2
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)

MEILI_HOST = os.environ.get("MEILI_HOST", "http://localhost:7700")
MEILI_MASTER_KEY = os.environ.get("MEILI_MASTER_KEY", "masterKeyToChange123")

try:
    meili_client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
except Exception as e:
    print(f"Could not connect to Meilisearch: {e}")
    meili_client = None

@app.before_request
def track_visitor():
    if request.path.startswith('/static') or request.path.startswith('/admin'):
        return
        
    visitor_id = request.cookies.get('visitor_id')
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
        request.new_visitor_id = visitor_id
    else:
        request.new_visitor_id = None
        
    request.visitor_id = visitor_id

@app.after_request
def set_visitor_cookie(response):
    if getattr(request, 'new_visitor_id', None):
        response.set_cookie('visitor_id', request.new_visitor_id, max_age=60*60*24*365*10)
    return response

@app.before_request
def log_page_view():
    if request.path.startswith('/static') or request.path.startswith('/admin') or request.path.startswith('/api'):
        return
        
    try:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.user_agent.string
        category = 'legitimate' if request.endpoint else 'suspicious'

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO page_views (session_id, path, ip_address, user_agent, category) VALUES (%s, %s, %s, %s, %s);",
            (getattr(request, 'visitor_id', 'unknown'), request.path, ip_address, user_agent, category)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error logging page view: {e}")

@app.route('/')
def index():
    q = request.args.get('q', '')
    title = f"Search for {q} - Hamadema" if q else "Hamadema - Sri Lanka's Hardware Search Engine"
    description = f"Compare prices for {q} across top Sri Lankan tech stores on Hamadema." if q else "Everything you need. Search products across multiple Sri Lankan sites instantly."
    
    return render_template('index.html', title=title, description=description, query=q)

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
        
        result_count = results.get('estimatedTotalHits', 0)
        
        # Log the search
        is_autocomplete = request.args.get('is_autocomplete', 'false').lower() == 'true'
        if query.strip() and not is_autocomplete:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO search_logs (session_id, query, result_count) VALUES (%s, %s, %s);",
                    (getattr(request, 'visitor_id', 'unknown'), query.strip(), result_count)
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Error logging search: {e}")

        return jsonify({
            'hits': results.get('hits', []),
            'totalHits': result_count,
            'limit': results.get('limit', limit),
            'offset': results.get('offset', offset),
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255),
                query VARCHAR(255),
                result_count INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS page_views (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255),
                path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute("ALTER TABLE page_views ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);")
        cursor.execute("ALTER TABLE page_views ADD COLUMN IF NOT EXISTS user_agent TEXT;")
        cursor.execute("ALTER TABLE page_views ADD COLUMN IF NOT EXISTS category VARCHAR(50);")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_stats_history (
                id SERIAL PRIMARY KEY,
                source_site VARCHAR(100),
                item_count INT,
                recorded_at DATE DEFAULT CURRENT_DATE,
                UNIQUE(source_site, recorded_at)
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
    top_searches = []
    zero_searches = []
    traffic = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Original Store Stats
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
            
        # Top 10 Searches
        cursor.execute("""
            SELECT query, COUNT(*) as count 
            FROM search_logs 
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT 10;
        """)
        top_searches = [{"query": r[0], "count": r[1]} for r in cursor.fetchall()]
        
        # Zero Result Searches
        cursor.execute("""
            SELECT query, COUNT(*) as count 
            FROM search_logs 
            WHERE result_count = 0 
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT 10;
        """)
        zero_searches = [{"query": r[0], "count": r[1]} for r in cursor.fetchall()]
        
        # Traffic (Last 7 Days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(DISTINCT session_id) as users, COUNT(*) as pageviews
            FROM page_views
            WHERE created_at >= CURRENT_DATE - INTERVAL '6 days' AND (category = 'legitimate' OR category IS NULL)
            GROUP BY DATE(created_at)
            ORDER BY date ASC;
        """)
        traffic = [{"date": r[0].strftime('%Y-%m-%d'), "users": r[1], "views": r[2]} for r in cursor.fetchall()]

        # Suspicious Logs (Security Audit)
        cursor.execute("""
            SELECT path, ip_address, user_agent, created_at 
            FROM page_views 
            WHERE category = 'suspicious' 
            ORDER BY created_at DESC 
            LIMIT 50;
        """)
        suspicious_logs = [{"path": r[0], "ip": r[1], "ua": r[2], "date": r[3].strftime('%Y-%m-%d %H:%M:%S')} for r in cursor.fetchall()]

        # Scraper History (Last 7 Days)
        cursor.execute("""
            SELECT recorded_at, source_site, item_count
            FROM scraper_stats_history
            WHERE recorded_at >= CURRENT_DATE - INTERVAL '6 days'
            ORDER BY recorded_at ASC, source_site ASC;
        """)
        scraper_history_raw = cursor.fetchall()
        
        # Format scraper history for Chart.js
        scraper_history_dict = {}
        for r in scraper_history_raw:
            date_str = r[0].strftime('%Y-%m-%d')
            site = r[1]
            count = r[2]
            if date_str not in scraper_history_dict:
                scraper_history_dict[date_str] = {}
            scraper_history_dict[date_str][site] = count
            
        scraper_history = [{"date": k, "stores": v} for k, v in scraper_history_dict.items()]

        cursor.close()
        conn.close()
    except Exception as e:
        error = str(e)
        suspicious_logs = []
        scraper_history = []
        
    return render_template('admin.html', stats=stats, top_searches=top_searches, zero_searches=zero_searches, traffic=traffic, suspicious_logs=suspicious_logs, scraper_history=scraper_history, error=error)

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

@app.route('/api/price-history/<doc_id>', methods=['GET'])
def get_price_history(doc_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT price_numeric, recorded_at FROM price_history WHERE doc_id = %s ORDER BY recorded_at ASC;",
            (doc_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        history = [{"price": r[0], "date": r[1].strftime('%Y-%m-%d')} for r in rows]
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

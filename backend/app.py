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

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not meili_client:
        return jsonify({"error": "Search engine not available"}), 500
        
    try:
        results = meili_client.index('items').search(query, {
            'limit': 20
        })
        return jsonify(results['hits'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Flask, request, jsonify
import hashlib

app = Flask(__name__)

@app.route('/', methods=['POST'])
def process_data():
    # 1. Parsing av inkommande JSON-data
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({'error': 'Ogiltig indata, "items" saknas'}), 400

    items = data.get('items', [])

    # 2. Datatransformering i minnet (sortering på värde)
    sorted_items = sorted(items, key=lambda x: x.get('value', 0), reverse=True)

    # 3. CPU-intensiv beräkningslogik (Hashing utan I/O-ventetid)
    processed_results = []
    for item in sorted_items:
        item_id = item.get('id', '')
        val = item.get('value', 0)
        
        # Simulera beräkningsarbete genom upprepad SHA-256-hashing
        raw_bytes = f"{item_id}:{val}".encode('utf-8')
        hashed_val = hashlib.sha256(raw_bytes).hexdigest()
        
        processed_results.append({
            'id': item_id,
            'original_value': val,
            'hash': hashed_val
        })

    # 4. JSON-serialisering och HTTP 200 OK-respons
    return jsonify({
        'status': 'success',
        'total_processed': len(processed_results),
        'results': processed_results
    }), 200

if __name__ == '__main__':
    # Körs via WSGI-server (t.ex. Gunicorn) i testmiljön
    app.run()
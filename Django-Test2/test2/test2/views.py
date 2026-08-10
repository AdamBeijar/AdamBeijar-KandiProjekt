from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import hashlib
import json

@csrf_exempt
def index(request):
    if request.method == 'POST':
        # Hantera POST-förfrågan
        data = request.body.decode('utf-8')

        if not data or 'items' not in data:
            return JsonResponse({'error': 'Ogiltig indata, "items" saknas'}, status=400)

        # Gör om data till JSON
        items = json.loads(data).get('items', [])

        sorted_items = sorted(items, key=lambda x: x.get('value', 0), reverse=True)

        processed_results = []
        for item in sorted_items:
            item_id = item.get('id', '')
            val = item.get('value', 0)

            raw_bytes = f"{item_id}:{val}".encode('utf-8')
            hashed_val = hashlib.sha256(raw_bytes).hexdigest()

            processed_results.append({
                'id': item_id,
                'original_value': val,
                'hash': hashed_val
            })
        return JsonResponse({
            'status': 'success',
            'total_processed': len(processed_results),
            'results': processed_results
        }, status=200)
from main.responses import HtmlResponse, JsonResponse 
import hashlib

def index(request):
    data = request.body
    if type(data) != dict and not data:
        return JsonResponse({"error": "Invalid data format. Expected JSON."}, status=400)
    items = data.get("items", [])

    sorted_items = sorted(items, key=lambda x: x.get("value", 0), reverse=True)

    processed_results = []
    for item in sorted_items:
        item_id = item.get("id", "")
        val = item.get("value", 0)
        raw_bytes = f"{item_id}:{val}".encode("utf-8")
        hashed_val = hashlib.sha256(raw_bytes).hexdigest()
        processed_results.append({
            "id": item_id,
            "original_value": val,
            "hash": hashed_val
        })

    return JsonResponse({
        "status": "success",
        "total_processed": len(processed_results),
        "results": processed_results
    }, status=200)
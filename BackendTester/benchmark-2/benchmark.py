import asyncio
import time
import json
import httpx
import pandas as pd
import matplotlib.pyplot as plt

# ================= CONFIGURATION =================
SERVICES = {
    "Flask (WSGI)": "http://localhost:5001/",
    #"Django": "http://192.168.0.107:8081/",
    #"Lättvikt": "http://192.168.0.107:8001/"
    
}

# Stegmodell för concurrency som testas automatiskt
CONCURRENCY_LEVELS = [10, 50, 100, 250, 500, 1000]
REQUESTS_PER_CONCURRENCY = 2000  # Antal pings per steg
TIMEOUT_SECONDS = 5.0

# Datapayload för Testfall 2 (In-memory datatransformering och CPU-hashing)
TEST2_PAYLOAD = {
    "items": [
        {"id": "A101", "value": 89.5},
        {"id": "B202", "value": 12.0},
        {"id": "C303", "value": 150.2},
        {"id": "D404", "value": 45.1},
        {"id": "E505", "value": 99.9}
    ]
}
# =================================================

async def send_ping(client, url, name, request_id, semaphore):
    async with semaphore:
        start_time = time.perf_counter()
        try:
            # Ändrat till POST med JSON-payload för Testfall 2
            response = await client.post(url, json=TEST2_PAYLOAD, timeout=TIMEOUT_SECONDS)
            latency = (time.perf_counter() - start_time) * 1000  # ms
            success = response.status_code == 200
            status = str(response.status_code)
        except Exception:
            latency = (time.perf_counter() - start_time) * 1000
            success = False
            status = "Timeout/Error"
            
        return {
            "Tjänst": name,
            "Request_ID": request_id,
            "Latency_ms": latency,
            "Success": success,
            "Status": status
        }

async def warmup_service(client, url):
    """Kör några hundra POST-anrop som kastas bort för att värma upp CPython och TCP-buffers."""
    print("  -> Värmer upp tjänsten för Testfall 2...")
    tasks = [client.post(url, json=TEST2_PAYLOAD, timeout=TIMEOUT_SECONDS) for _ in range(200)]
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(1)

async def benchmark_run(client, url, name, concurrency, total_requests):
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [send_ping(client, url, name, i, semaphore) for i in range(total_requests)]
    
    # Mät EXAKT väggtid för alla anrop i steget
    start_time = time.perf_counter()
    results = await asyncio.gather(*tasks)
    wall_time = time.perf_counter() - start_time
    
    return results, wall_time

async def main():
    print("=" * 80)
    print("Startar automatiserat prestandatest för TESTFALL 2 (CPU & Databearbetning)")
    print(f"Nivåer: {CONCURRENCY_LEVELS} | Anrop/nivå: {REQUESTS_PER_CONCURRENCY}")
    print("=" * 80)
    
    summary_results = []
    
    for name, url in SERVICES.items():
        print(f"\n>>> Testar {name} ({url}) <<<")
        
        # Sätt max connections så att httpx inte begränsar i förtid
        max_conn = max(CONCURRENCY_LEVELS)
        limits = httpx.Limits(max_keepalive_connections=max_conn, max_connections=max_conn)
        
        async with httpx.AsyncClient(limits=limits) as client:
            # 1. Warmup
            await warmup_service(client, url)
            
            # 2. Stega igenom alla concurrency-nivåer
            for conc in CONCURRENCY_LEVELS:
                print(f"  Running concurrency: {conc} ... ", end="", flush=True)
                
                raw_results, wall_time = await benchmark_run(client, url, name, conc, REQUESTS_PER_CONCURRENCY)
                
                # Bearbeta data för denna nivå
                df = pd.DataFrame(raw_results)
                df_success = df[df["Success"] == True]
                
                failures = len(df) - len(df_success)
                rps = len(df_success) / wall_time if wall_time > 0 else 0
                
                if not df_success.empty:
                    mean_val = df_success["Latency_ms"].mean()
                    p50_val = df_success["Latency_ms"].median()
                    p95_val = df_success["Latency_ms"].quantile(0.95)
                    p99_val = df_success["Latency_ms"].quantile(0.99)
                else:
                    mean_val = p50_val = p95_val = p99_val = 0
                
                summary_results.append({
                    "Tjänst": name,
                    "Concurrency": conc,
                    "RPS": round(rps, 1),
                    "Medel_ms": round(mean_val, 1),
                    "p50_ms": round(p50_val, 1),
                    "p95_ms": round(p95_val, 1),
                    "p99_ms": round(p99_val, 1),
                    "Fel": failures,
                    "WallTime_s": round(wall_time, 2)
                })
                
                print(f"Klar! RPS: {rps:.1f} | p95: {p95_val:.1f} ms | Fel: {failures}")
                await asyncio.sleep(1)  # Paus mellan steg

    # Spara resultat till JSON
    json_filename = "benchmark_results_testfall2.json"
    with open(json_filename, "w") as f:
        json.dump(summary_results, f, indent=4)
    print(f"\nResultat sparade till '{json_filename}'")

    # Convert to DataFrame for plotting
    df_res = pd.DataFrame(summary_results)
    
    # 3. Rita grafer anpassade för avhandlingen
    plt.figure(figsize=(14, 5))

    # Graf 1: Concurrency vs Throughput (RPS)
    plt.subplot(1, 2, 1)
    for name in SERVICES.keys():
        sub = df_res[df_res["Tjänst"] == name]
        plt.plot(sub["Concurrency"], sub["RPS"], marker='o', linewidth=2, label=name)
    plt.title("Testfall 2: Throughput (RPS) vs Samtida anslutningar")
    plt.xlabel("Concurrency (Samtida anrop)")
    plt.ylabel("Requests Per Second (RPS)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    # Graf 2: Concurrency vs p95 Latency
    plt.subplot(1, 2, 2)
    for name in SERVICES.keys():
        sub = df_res[df_res["Tjänst"] == name]
        plt.plot(sub["Concurrency"], sub["p95_ms"], marker='s', linewidth=2, label=name)
    plt.title("Testfall 2: p95 Latens vs Samtida anslutningar")
    plt.xlabel("Concurrency (Samtida anrop)")
    plt.ylabel("95:e percentilen svarstid (ms)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    plt.tight_layout()
    chart_filename = "benchmark_testfall2_chart.png"
    plt.savefig(chart_filename, dpi=300)
    print(f"Graf sparad till '{chart_filename}'")
    plt.show()

if __name__ == "__main__":
    asyncio.run(main())
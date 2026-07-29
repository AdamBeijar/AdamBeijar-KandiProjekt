import asyncio
import time
import json
import httpx
import pandas as pd
import matplotlib.pyplot as plt

# ================= CONFIGURATION =================
SERVICES = {
    "Flask (WSGI)": "http://192.168.0.109:5000/",
    "Django": "http://192.168.0.109:8080/",
    "Lättvikt": "http://192.168.0.109:8000/"
}

TOTAL_REQUESTS = 2000    # Totalt antal pings per tjänst
CONCURRENT_LIMIT = 100   # Hur många anrop som körs samtidigt (concurrency)
TIMEOUT_SECONDS = 5.0    # Tid innan ett anrop räknas som misslyckat
# =================================================

async def send_ping(client, url, name, request_id, semaphore):
    async with semaphore:
        start_time = time.perf_counter()
        try:
            response = await client.get(url, timeout=TIMEOUT_SECONDS)
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

async def benchmark_service(name, url):
    print(f"Kör test mot {name} ({url})...")
    semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
    
    limits = httpx.Limits(max_keepalive_connections=CONCURRENT_LIMIT, max_connections=CONCURRENT_LIMIT)
    async with httpx.AsyncClient(limits=limits) as client:
        # Skapa och kör alla anrop asynkront (skickar med ett unikt Request_ID för tidslinjen)
        tasks = [send_ping(client, url, name, i, semaphore) for i in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
    return results

async def main():
    print("=" * 70)
    print(f"Startar prestandatest: {TOTAL_REQUESTS} anrop (concurrency: {CONCURRENT_LIMIT})")
    print("=" * 70)
    
    all_raw_data = []
    
    for name, url in SERVICES.items():
        results = await benchmark_service(name, url)
        all_raw_data.extend(results)
        # Liten paus mellan testerna så att portar hinner stängas ordentligt
        await asyncio.sleep(1)
        
    # 1. Konvertera rådata till en Pandas DataFrame
    df = pd.DataFrame(all_raw_data)
    
    # Separera lyckade och misslyckade anrop
    df_success = df[df["Success"] == True]
    
    # 2. Beräkna statistik och percentiler via Pandas per tjänst
    summary_list = []
    
    print("\n" + "=" * 35 + " RESULTAT " + "=" * 35)
    
    # Skapa tabell-headers
    headers = ["Tjänst", "RPS", "Medel", "p50 (Med)", "p90", "p95", "p99", "Max", "Fel"]
    header_row = " | ".join(f"{h:<12}" for h in headers)
    separator = "-|-".join("-" * 12 for _ in headers)
    print(header_row)
    print(separator)
    
    for name in SERVICES.keys():
        service_all = df[df["Tjänst"] == name]
        service_success = df_success[df_success["Tjänst"] == name]
        
        total_duration = service_all["Latency_ms"].sum() / 1000 / CONCURRENT_LIMIT # Uppskattad väggtid baserat på concurrency
        # Mer exakt väggtid beräknas här istället från rådatans totala spann under sekventiell körning
        
        # Räkna faktiska misslyckade
        failures = len(service_all) - len(service_success)
        
        # Räkna ut mätvärden om det finns lyckade anrop
        if not service_success.empty:
            mean_val = service_success["Latency_ms"].mean()
            p50_val = service_success["Latency_ms"].median()
            p90_val = service_success["Latency_ms"].quantile(0.90)
            p95_val = service_success["Latency_ms"].quantile(0.95)
            p99_val = service_success["Latency_ms"].quantile(0.99)
            max_val = service_success["Latency_ms"].max()
            rps_val = len(service_all) / (service_all["Latency_ms"].sum() / 1000 / CONCURRENT_LIMIT) # Alternativ väggtid-beräkning
        else:
            mean_val = p50_val = p90_val = p95_val = p99_val = max_val = rps_val = 0
            
        # Fixa till RPS-beräkningen baserat på den faktiska tiden tjänsten tog (grov uppskattning utifrån testkörningen)
        # För exakt RPS tar vi totalt antal anrop dividerat med summan av latency justerat för concurrency
        rps_val = len(service_all) / (service_all["Latency_ms"].sum() / 1000 / CONCURRENT_LIMIT)
        if rps_val > (TOTAL_REQUESTS * 2): # Säkerhetsspärr för extremt snabba lokala svar
            rps_val = TOTAL_REQUESTS / (service_success["Latency_ms"].mean() / 1000) if not service_success.empty else 0

        # Formatera raden
        row_str = (
            f"{name:<12} | {rps_val:<12.1f} | {mean_val:<12.1f} | {p50_val:<12.1f} | "
            f"{p90_val:<12.1f} | {p95_val:<12.1f} | {p99_val:<12.1f} | {max_val:<12.1f} | {failures:<12}"
        )
        print(row_str)
        
        # Spara undan i ordbok för JSON-export
        summary_list.append({
            "Tjänst": name, "RPS": round(rps_val, 1), "Medel_ms": round(mean_val, 1),
            "p50_ms": round(p50_val, 1), "p90_ms": round(p90_val, 1), "p95_ms": round(p95_val, 1),
            "p99_ms": round(p99_val, 1), "Max_ms": round(max_val, 1), "Misslyckade": failures
        })
        
    print("=" * 115)
    
    # Spara resultat till JSON
    with open("benchmark_results.json", "w") as f:
        json.dump(summary_list, f, indent=4)
    print("Resultaten har sparats till 'benchmark_results.json'")
    
    # 3. Rita grafer med Matplotlib
    plt.figure(figsize=(14, 6))
    
    # Graf 1: Boxplot över latensfördelning (visar spridning, median och p95/p99 utan extrema outliers)
    plt.subplot(1, 2, 1)
    df_success.boxplot(column="Latency_ms", by="Tjänst", ax=plt.gca(), showfliers=False)
    plt.title("Latensfördelning per arkitektur\n(Exklusive extrema outliers)")
    plt.ylabel("Svarstid (ms)")
    plt.xlabel("")
    plt.grid(True, linestyle="--", alpha=0.6)
    
    # Graf 2: Rullande medelvärde över tid (kronologiskt efter Request_ID)
    plt.subplot(1, 2, 2)
    for name in SERVICES.keys():
        service_data = df_success[df_success["Tjänst"] == name].sort_values("Request_ID")
        if not service_data.empty:
            # Rullande fönster på 50 anrop för att jämna ut spikar och visa den faktiska trenden
            rolling_mean = service_data["Latency_ms"].rolling(window=50, min_periods=1).mean()
            plt.plot(service_data["Request_ID"], rolling_mean, label=name, linewidth=2)
            
    plt.title("Rullande medelvärde av svarstider\n(Fönster: 50 anrop)")
    plt.xlabel("Anropsnummer (kronologiskt)")
    plt.ylabel("Svarstid (ms)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    
    plt.tight_layout()
    plt.suptitle("")  # Ta bort Pandas autogenererade övergripande titel
    
    # Spara grafen
    plt.savefig("benchmark_chart.png", dpi=300)
    print("Prestandagraferna har sparats till 'benchmark_chart.png'")
    plt.show()

if __name__ == "__main__":
    asyncio.run(main())
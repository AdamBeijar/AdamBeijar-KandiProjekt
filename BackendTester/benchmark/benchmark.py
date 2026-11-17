"""
Benchmark för Testfall 1 och 2 som använder oha som lastgenerator.

Python-skriptet styr bara stegen (concurrency-nivåer och omgångar), läser in
ohas JSON-resultat och ritar graferna. Själva förfrågningarna skickas av oha,
så att klienten inte blir flaskhalsen.

Varje test körs RUNS gånger. Rådata för varje omgång sparas, och graferna
visar medelvärdet över omgångarna med standardavvikelsen som felstaplar.

Kör:  python benchmark_oha.py 1     (Testfall 1, GET ping)
      python benchmark_oha.py 2     (Testfall 2, POST med JSON)
"""
import json
import subprocess
import sys
import time

import pandas as pd
import matplotlib.pyplot as plt

# ================= KONFIGURATION =================
HOST = "192.168.0.107"

TESTS = {
    1: {
        "namn": "Testfall 1",
        "services": {
            "Flask (WSGI)": f"http://{HOST}:5000/",
            "Django": f"http://{HOST}:8088/",
            "Lättvikt": f"http://{HOST}:8000/",
        },
        "method": "GET",
        "payload": None,
    },
    2: {
        "namn": "Testfall 2",
        "services": {
            "Flask (WSGI)": f"http://{HOST}:5001/",
            "Django": f"http://{HOST}:8081/",
            "Lättvikt": f"http://{HOST}:8001/",
        },
        "method": "POST",
        "payload": {
            "items": [
                {"id": "A101", "value": 89.5},
                {"id": "B202", "value": 12.0},
                {"id": "C303", "value": 150.2},
                {"id": "D404", "value": 45.1},
                {"id": "E505", "value": 99.9},
            ]
        },
    },
}

RUNS = 5                              # antal omgångar per test
CONCURRENCY_LEVELS = [10, 50, 100, 250, 500, 1000]
REQUESTS_PER_CONCURRENCY = 50000
WARMUP_REQUESTS = 200
TIMEOUT_SECONDS = 5
PAUSE_BETWEEN_LEVELS_S = 5            # låter TIME_WAIT-portar frigöras
PAUSE_BETWEEN_RUNS_S = 30
MAX_ERROR_RATE = 0.01                 # varna om mer än 1 % av förfrågningarna misslyckas

# Nyare oha-versioner använder "--output-format json", äldre "--json".
# Kolla med:  oha --help   och byt vid behov.
JSON_FLAG = ["--output-format", "json"]
# =================================================


def run_oha(url, n, c, method, payload):
    """Kör oha en gång och returnerar resultatet som en dict."""
    cmd = ["oha", "-n", str(n), "-c", str(c), "-t", f"{TIMEOUT_SECONDS}s",
           "--no-tui", *JSON_FLAG, "-m", method]
    if payload is not None:
        cmd += ["-T", "application/json", "-d", json.dumps(payload)]
    cmd.append(url)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"oha misslyckades:\n{proc.stderr}")
    return json.loads(proc.stdout)


def ms(value):
    """oha anger tider i sekunder -> omvandla till ms."""
    return round((value or 0) * 1000, 1)


def run_once(test, run_nr):
    """Kör alla ramverk och alla nivåer en gång. Returnerar en lista med rader."""
    rows = []
    for name, url in test["services"].items():
        print(f"\n>>> Omgång {run_nr}/{RUNS} – {name} ({url}) <<<")

        # Uppvärmning (resultatet kastas)
        run_oha(url, WARMUP_REQUESTS, 10, test["method"], test["payload"])
        time.sleep(1)

        for conc in CONCURRENCY_LEVELS:
            res = run_oha(url, REQUESTS_PER_CONCURRENCY, conc,
                          test["method"], test["payload"])
            s = res["summary"]
            p = res["latencyPercentiles"]
            ok = res["statusCodeDistribution"].get("200", 0)
            fel = REQUESTS_PER_CONCURRENCY - ok
            felandel = fel / REQUESTS_PER_CONCURRENCY

            row = {
                "Omgång": run_nr,
                "Tjänst": name,
                "Concurrency": conc,
                "RPS": round(s["requestsPerSec"], 1),
                "Medel_ms": ms(s["average"]),
                "p50_ms": ms(p["p50"]),
                "p95_ms": ms(p["p95"]),
                "p99_ms": ms(p["p99"]),
                "Fel": fel,
                "Felandel": round(felandel, 4),
                "Feltyper": res.get("errorDistribution", {}),
                "WallTime_s": round(s["total"], 2),
            }
            rows.append(row)

            varning = "  <-- VARNING: hög felandel, kontrollera klienten!" if felandel > MAX_ERROR_RATE else ""
            print(f"  c={conc:>4}: RPS {row['RPS']:>8} | p95 {row['p95_ms']:>7} ms | fel {fel}{varning}")
            time.sleep(PAUSE_BETWEEN_LEVELS_S)
    return rows


def main(test_nr):
    test = TESTS[test_nr]
    print(f"Startar {test['namn']} med oha | {RUNS} omgångar | nivåer: {CONCURRENCY_LEVELS}")

    all_rows = []
    for run_nr in range(1, RUNS + 1):
        all_rows += run_once(test, run_nr)
        if run_nr < RUNS:
            print(f"\nPaus {PAUSE_BETWEEN_RUNS_S} s före nästa omgång...")
            time.sleep(PAUSE_BETWEEN_RUNS_S)

    # 1. Rådata för varje omgång
    raw_file = f"benchmark_results_testfall{test_nr}_oha_raw.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=4, ensure_ascii=False)
    print(f"\nRådata sparad till '{raw_file}'")

    # 2. Sammanställning: medelvärde och standardavvikelse över omgångarna
    df = pd.DataFrame(all_rows)
    metrics = ["RPS", "Medel_ms", "p50_ms", "p95_ms", "p99_ms", "Fel"]
    agg = df.groupby(["Tjänst", "Concurrency"], sort=False)[metrics].agg(["mean", "std"])
    agg.columns = [f"{m}_{stat}" for m, stat in agg.columns]
    agg = agg.round(1).reset_index()

    summary_file = f"benchmark_results_testfall{test_nr}_oha.json"
    agg.to_json(summary_file, orient="records", indent=4, force_ascii=False)
    print(f"Sammanställning sparad till '{summary_file}'")

    # 3. Grafer: medelvärde med standardavvikelse som felstaplar
    plt.figure(figsize=(14, 5))

    plt.subplot(1, 2, 1)
    for name in test["services"]:
        sub = agg[agg["Tjänst"] == name]
        plt.errorbar(sub["Concurrency"], sub["RPS_mean"], yerr=sub["RPS_std"],
                     marker="o", linewidth=2, capsize=4, label=name)
    plt.title(f"{test['namn']}: Genomströmning (medel av {RUNS} omgångar)")
    plt.xlabel("Samtidiga anrop")
    plt.ylabel("Förfrågningar per sekund")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    plt.subplot(1, 2, 2)
    for name in test["services"]:
        sub = agg[agg["Tjänst"] == name]
        plt.errorbar(sub["Concurrency"], sub["p95_ms_mean"], yerr=sub["p95_ms_std"],
                     marker="s", linewidth=2, capsize=4, label=name)
    plt.title(f"{test['namn']}: p95-latens (medel av {RUNS} omgångar)")
    plt.xlabel("Samtidiga anrop")
    plt.ylabel("95:e percentilen (ms)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    plt.tight_layout()
    chart = f"benchmark_testfall{test_nr}_oha_chart.png"
    plt.savefig(chart, dpi=300)
    print(f"Graf sparad till '{chart}'")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
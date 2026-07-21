import time
import os
from Crypto.Cipher import AES


# --- Configuration ---
PAYLOAD = b"A" * 32
ITERATIONS = 1000
WARM_UP_RUNS = 50
LOCAL_KEY = os.urandom(32)
IV = os.urandom(16)


# --- Execution ---
latencies = []


print(f"Starting {ITERATIONS} LOCAL AES-256 Encrypt calls...")


for i in range(ITERATIONS):
   start_time = time.perf_counter() 


   cipher = AES.new(LOCAL_KEY, AES.MODE_CFB, IV)
   cipher.encrypt(PAYLOAD)


   end_time = time.perf_counter()
   latency_ms = (end_time - start_time) * 1000
   if i >= WARM_UP_RUNS:
       latencies.append(latency_ms)


# --- Analysis ---
if latencies:
   latencies.sort()


   valid_count = len(latencies)
   avg_latency = sum(latencies) / valid_count


   p95_index = int(len(latencies) * 0.95) - 1
   p99_index = int(len(latencies) * 0.99) - 1


   p95_latency = latencies[p95_index]
   p99_latency = latencies[p99_index]


   print("\n--- BASELINE Latency Results (Local Crypto) ---")
   print(f"Tests Completed: {valid_count} (excluding warm-up)")
   print(f"Average Latency: {avg_latency:.6f} ms")
   print(f"P95 Latency: {p95_latency:.6f} ms (95% of requests are faster than this)")
   print(f"P99 Latency: {p99_latency:.6f} ms (99% of requests are faster than this)")
else:
   print("No valid latency data collected.")

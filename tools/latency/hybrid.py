import time
import base64
from google.cloud import kms_v1


# --- Configuration ---
PAYLOAD = b"A" * 32
ITERATIONS = 1000
WARM_UP_RUNS = 50
KEY_RESOURCE_NAME = "projects/${var.kms_project_id}/locations/${var.kms_location}/keyRings/${var.kms_key_ring}/cryptoKeys/${var.kms_key_name}"


# --- Execution ---
client = kms_v1.KeyManagementServiceClient()
latencies = []


print(f"Starting {ITERATIONS} KMS Encrypt calls for key: {KEY_RESOURCE_NAME}...")


for i in range(ITERATIONS):
   start_time = time.perf_counter()  # begins measurements
  
   try:
       response = client.encrypt(name=KEY_RESOURCE_NAME, plaintext=PAYLOAD)
      
   except Exception as e:
       print(f"Error during KMS call at iteration {i}: {e}")
       continue
      
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


   print("\n--- KMS Latency Results ---")
   print(f"Tests Completed: {valid_count} (excluding warm-up)")
   print(f"Average Latency: {avg_latency:.6f} ms")
   print(f"P95 Latency: {p95_latency:.6f} ms (95% of requests are faster than this)")
   print(f"P99 Latency: {p99_latency:.6f} ms (99% of requests are faster than this)")
else:
   print("No valid latency data collected.")
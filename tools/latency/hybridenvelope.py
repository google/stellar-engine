# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import os
from Crypto.Cipher import AES
from google.cloud import kms_v1


# --- Global Configuration ---
FULL_TEST_ITERATIONS = 1000
WARM_UP_RUNS = 50


# KMS Key Configuration (The Master Key)
KEY_RESOURCE_NAME = "projects/${var.kms_project_id}/locations/${var.kms_location}/keyRings/${var.kms_key_ring}/cryptoKeys/${var.kms_key_name}"
CLIENT = kms_v1.KeyManagementServiceClient()


BULK_PAYLOAD_SIZE = (1024 * 1024)  # 1 MB
IV_LENGTH = 16


# --- Execution & Data Collection ---
kms_latencies = []
local_bulk_latencies = []
full_envelope_latencies = []


print(f"Starting {FULL_TEST_ITERATIONS} Envelope Encryption Cycles...")


for i in range(FULL_TEST_ITERATIONS):
   BULK_PAYLOAD = os.urandom(BULK_PAYLOAD_SIZE)
  
   DEK_LOCAL = os.urandom(32)
  
   # --- Measure Sub-Process A: Remote Encryption (KMS API Call) ---
   start_time_kms = time.perf_counter()
   start_time_full = time.perf_counter() # Start timer for the whole process


   try:
       kms_response = CLIENT.encrypt(name=KEY_RESOURCE_NAME, plaintext=DEK_LOCAL)
       ENCRYPTED_DEK = kms_response.ciphertext
      
   except Exception as e:
       print(f"FATAL ERROR at iteration {i}: KMS encryption failed: {e}")
       break # Exit the loop immediately on fatal error


   end_time_kms = time.perf_counter()
   kms_latency = (end_time_kms - start_time_kms) * 1000
  
   # --- Measure Sub-Process B: Local Encryption (Bulk Data) ---
   start_time_local = time.perf_counter()


   try:
       cipher_local = AES.new(DEK_LOCAL, AES.MODE_CFB, IV=os.urandom(IV_LENGTH))
       ENCRYPTED_DATA = cipher_local.encrypt(BULK_PAYLOAD)
   except Exception as e:
       print(f"FATAL ERROR at iteration {i}: Local encryption failed: {e}")
       break


   end_time_local = time.perf_counter()
   end_time_full = time.perf_counter() 
   local_latency = (end_time_local - start_time_local) * 1000
   full_latency = (end_time_full - start_time_full) * 1000


   if i >= WARM_UP_RUNS:
       kms_latencies.append(kms_latency)
       local_bulk_latencies.append(local_latency)
       full_envelope_latencies.append(full_latency)




# --- Analysis ---
def analyze_latency(latencies, name):
   if not latencies:
       print(f"\n--- {name} Results ---")
       print("No valid data collected.")
       return


   latencies.sort()
   valid_count = len(latencies)
   avg_latency = sum(latencies) / valid_count
  
   p95_index = int(valid_count * 0.95) - 1
   p99_index = int(valid_count * 0.99) - 1
  
   p95_latency = latencies[p95_index]
   p99_latency = latencies[p99_index]


   print(f"\n--- {name} Results ---")
   print(f"Tests Completed: {valid_count} (excluding warm-up)")
   print(f"Average Latency: {avg_latency:.3f} ms")
   print(f"P95 Latency: {p95_latency:.3f} ms")
   print(f"P99 Latency: {p99_latency:.3f} ms")


analyze_latency(full_envelope_latencies, "FULL ENVELOPE ENCRYPTION")
analyze_latency(kms_latencies, "KMS DEK ENCRYPTION ONLY")
analyze_latency(local_bulk_latencies, "LOCAL BULK ENCRYPTION ONLY")

#!/bin/bash
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

set -u

KC_HOME="/opt/keycloak"
CONFIG_FILE="config.env"
DELIMITER="@"

# --- Load Configuration ---
if [ -f "$CONFIG_FILE" ]; then
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
    echo "Loaded configuration from $CONFIG_FILE"
else
    echo "Error: Configuration file not found. Please create config.env"
    exit 1
fi

echo "============================================="
echo "   Keycloak Setup: Realm & Realm Admin       "
echo "============================================="
echo "Target Realm: $REALM_NAME"
echo "Realm Admin:  $REALM_ADMIN_EMAIL"
echo "---------------------------------------------"

# --- 1. Connect to Pod ---

echo ""
echo "Finding Keycloak Pod..."
POD_NAME=$(kubectl get pod -n "$NAMESPACE" -l "$POD_LABEL" -o jsonpath="{.items[0].metadata.name}")

if [ -z "$POD_NAME" ]; then
  echo "Error: No Keycloak pod found."
  exit 1
fi
echo "Found Pod: $POD_NAME"

# Alias for clean execution
function kcadm_wrapper() {
    kubectl exec -i -n "$NAMESPACE" "$POD_NAME" -- $KC_HOME/bin/kcadm.sh "$@"
}

# --- 2. Authenticate ---

echo "--- 🔑 Authenticating CLI ---"
if ! printf '%s\n' "$BOOTSTRAP_PASS" | kcadm_wrapper config credentials --server http://localhost:8080 --realm master --user "$BOOTSTRAP_USER" > /dev/null; then
    echo "FATAL: Login failed. Check BOOTSTRAP_PASS in your .env file."
    exit 1
fi
echo "Authenticated successfully."

# --- 3. Create Realm ---

echo "--- Configuring Realm: $REALM_NAME ---"
if kcadm_wrapper get realms/"$REALM_NAME" >/dev/null 2>&1; then
    echo "Realm '$REALM_NAME' already exists. Skipping creation."
else
    kcadm_wrapper create realms -s realm="$REALM_NAME" -s enabled=true -s displayName="$REALM_DISPLAY_NAME"
    echo "Realm created."
fi

# --- 4. Loop Through User List ---

echo "--- Provisioning User List ---"

for USER_ENTRY in $USER_LIST; do
    # Split "email:pass" into variables
    U_EMAIL="${USER_ENTRY%%:*}"
    U_PASS="${USER_ENTRY##*:}"

    if [ -z "$U_EMAIL" ] || [ -z "$U_PASS" ]; then
        echo "Skipping invalid entry: $USER_ENTRY"
        continue
    fi

    echo "   > Processing: $U_EMAIL"
    
    # Check if user exists
    U_CHECK=$(kcadm_wrapper get users -r "$REALM_NAME" -q email="$U_EMAIL" 2>/dev/null)
    
    if [[ "$U_CHECK" == *"$U_EMAIL"* ]]; then
        echo "     User exists. Skipping..."
    else
        U_NAME=$(echo "$U_EMAIL" | cut -d"$DELIMITER" -f1)
        kcadm_wrapper create users -r "$REALM_NAME" \
            -s username="$U_NAME" \
            -s email="$U_EMAIL" \
            -s enabled=true \
            -s emailVerified=true \
            -s firstName="Standard" -s lastName="User"
        
        printf '%s\n' "$U_PASS" | kcadm_wrapper set-password -r "$REALM_NAME" --username "$U_NAME" --temporary=false
        echo "     Created."
    fi
done

# --- 5. Create Test Client ---

echo "--- Configuring Test App Client ---"
if kcadm_wrapper get clients -r "$REALM_NAME" -q clientId=test-app 2>/dev/null | grep -q "test-app"; then
    echo "Client 'test-app' already exists."
else
    kcadm_wrapper create clients -r "$REALM_NAME" \
        -s clientId=test-app \
        -s enabled=true \
        -s protocol=openid-connect \
        -s publicClient=true \
        -s directAccessGrantsEnabled=true \
        -s 'redirectUris=["https://www.google.com"]' \
        -s 'webOrigins=["+"]'
    echo "Client 'test-app' created."
fi

echo ""
echo "Provisioning Complete!"
echo "Realm Admin Login: https://keycloak.landingzone.example.com/admin/$REALM_NAME/console"
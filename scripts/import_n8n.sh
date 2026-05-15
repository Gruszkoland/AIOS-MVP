#!/bin/bash
N8N_URL=http://localhost:5678
USER=admin
PASS=KSUSg3VNKzj2kH7FjZhoiw

for f in /opt/adrion-system/n8n-workflows/*.json; do
  echo -n "Importing $(basename $f)... "
  RES=$(curl -s -o /tmp/n8n_resp.json -w '%{http_code}' -X POST $N8N_URL/api/v1/workflows \
    -H 'Content-Type: application/json' \
    -u $USER:$PASS \
    -d @"$f")
  if [ "$RES" -eq 200 ] || [ "$RES" -eq 201 ]; then
    ID=$(python3 -c 'import json; d=json.load(open("/tmp/n8n_resp.json")); print(d.get("id","?"))' 2>/dev/null)
    echo "OK id=$ID"
  else
    echo "FAIL HTTP=$RES"
    head -3 /tmp/n8n_resp.json 2>/dev/null
  fi
done
echo "Done."

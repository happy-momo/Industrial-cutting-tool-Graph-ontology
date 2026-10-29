#!/usr/bin/env bash
set -euo pipefail
NAME=pilot-neo4j
# Ports 7474/7687 are occupied by another project's Neo4j (neo4j-apoc-compose); this
# pilot uses non-conflicting host ports 7475 (http) and 7689 (bolt).
if ! docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
  echo "Starting Neo4j 5 community on bolt://localhost:7689 (user neo4j / pass pilotsecret)"
  docker run -d --name "$NAME" \
    -p 127.0.0.1:7475:7474 -p 127.0.0.1:7689:7687 \
    -e NEO4J_AUTH=neo4j/pilotsecret \
    neo4j:5-community
else
  echo "Container ${NAME} exists; starting if stopped."
  docker start "$NAME" >/dev/null 2>&1 || true
fi
echo "Waiting for bolt ready..."
for i in $(seq 1 60); do
  if python3 -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7689', auth=('neo4j','pilotsecret')).verify_connectivity()" 2>/dev/null; then
    echo "Neo4j ready."
    exit 0
  fi
  sleep 2
done
echo "Timed out waiting for Neo4j"
exit 1
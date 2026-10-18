#!/bin/bash
# Deploys an API image on the EC2 host. Sent by the deploy workflow through SSM Run Command, which runs it as root.
# Usage: ec2-deploy.sh <image>
set -euo pipefail

IMAGE="$1"
REGION=us-east-1
export HOME=/root # SSM Run Command does not set it
ENV_FILE=/etc/logos/api.env
CONTAINER=logos-api

parameter() {
  aws ssm get-parameter --region "$REGION" --name "/logos/$1" --with-decryption --query Parameter.Value --output text
}

# Read into variables first: a failing command substitution inside echo would not stop the script.
database_url=$(parameter database-url)
jwt_secret=$(parameter jwt-secret)

install -d -m 700 /etc/logos
umask 077
{
  echo "ENVIRONMENT=production"
  echo "DATABASE_URL=$database_url"
  echo "JWT_SECRET=$jwt_secret"
} >"$ENV_FILE"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${IMAGE%%/*}"
docker pull --quiet "$IMAGE"

# Migrations and seed run before the swap: if they fail, the current API keeps serving.
docker run --rm --env-file "$ENV_FILE" "$IMAGE" sh -c "alembic upgrade head && python -m scripts.seed"

docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" --restart unless-stopped -p 80:8000 --env-file "$ENV_FILE" "$IMAGE" >/dev/null

for _ in $(seq 1 30); do
  if curl -fsS http://localhost/api/health >/dev/null; then
    echo "API healthy: $IMAGE"
    docker image prune -af >/dev/null
    exit 0
  fi
  sleep 2
done

echo "API did not become healthy" >&2
docker logs --tail 50 "$CONTAINER" >&2
exit 1

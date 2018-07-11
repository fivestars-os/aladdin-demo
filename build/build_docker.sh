#!/usr/bin/env bash

echo "Building aladdin-demo docker image (~30 seconds)"

BUILD_PATH="$(cd "$(dirname "$0")"; pwd)"
PROJ_ROOT="$(cd "$BUILD_PATH/.." ; pwd)"

docker_build() {
    typeset name="$1" dockerfile="$2" context="$3"
    TAG="$name:${HASH}"
    docker build -t $TAG -f $dockerfile $context
}
cd "$PROJ_ROOT"

docker_build "aladdin-demo" "app/Dockerfile" "app"

#aws login because we are pulling from ecr for base image
$(aws --profile sandbox ecr get-login --no-include-email)
docker_build "aladdin-demo-commands" "app/commands_app/Dockerfile" "app"

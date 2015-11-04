#!/bin/bash

DIR=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
TOMATODIR="$DIR"/../..

function tomato-write_version_info() {
    # first argument: output directory
    # second argument: dpkg package
  git describe --tags | cut -f1,2 -d'-' > "$1"/version
}

function tomato-delete_version_info() {
    # first argument: output directory of write_version_info
    if [ -e "$1"/version ]; then
        rm "$1"/version
    fi
}

function tomato-db-start () {
  mkdir -p "$DIR"/mongodb-data
  docker run -d -v "$DIR"/mongodb-data:/data/db -p 127.0.0.1:27017:27017 --name mongodb mongo:latest --storageEngine wiredTiger
  docker start mongodb
}

function tomato-db-sql () {
  docker run -it --link mongodb:mongo --rm mongo sh \
             -c 'exec mongo "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT/tomato"'
}

function tomato-db-dump () {
  BACKUP_DIR="$DIR"/mongodb-backup
  mkdir -p "$BACKUP_DIR"
  ARCHIVE="$1"
  if [ "$ARCHIVE" == "" ]; then
    ARCHIVE="$DIR/mongodb-dump-$(date +%F).tar.gz"
  fi
  docker run -it --link mongodb:mongo -v "$BACKUP_DIR":/backup --rm mongo sh \
             -c 'mongodump -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" -d tomato --out /backup; chmod -R ogu+rwX /backup'
  tar -czf "$ARCHIVE" -C "$BACKUP_DIR" .
  rm -rf "$BACKUP_DIR"
}

function tomato-db-restore () {
  BACKUP_DIR="$DIR"/mongodb-backup
  rm -rf "$BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
  ARCHIVE="$1"
  if ! [ -f "$ARCHIVE" ]; then
    echo "Archive not found" >&2
    return 1
  fi
  tar -xzf "$ARCHIVE" -C "$BACKUP_DIR"
  docker run -it --link mongodb:mongo -v "$BACKUP_DIR":/backup --rm mongo sh \
             -c 'exec mongorestore -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" "/backup" --drop'
  rm -rf "$BACKUP_DIR"
}

function tomato-db-stop () {
  docker stop mongodb
  docker rm mongodb
}


function tomato-backend-start () {
  mkdir -p "$DIR"/backend/{config,data,logs}
  tomato-write_version_info "$DIR"/backend/config
  docker run -d -v "$TOMATODIR"/backend:/code -v "$TOMATODIR"/shared:/shared \
             -v "$DIR"/backend/config:/config -v "$DIR"/backend/data:/data -v "$DIR"/backend/logs:/logs \
             --link mongodb:db -p 8006:8006 -p 8000:8000 -p 8001:8001 -p 8002:8002 \
             -p 8010:8010 -p 8011:8011 -p 8012:8012 -p 8013:8013 -p 8014:8014 -p 8015:8015 \
             -p 8016:8016 -p 8017:8017 -p 8018:8018 -p 8019:8019 -p 8020:8020 \
             --dns 131.246.9.116 -e "TIMEZONE=Europe/Berlin" --name tomato-backend tomato-backend
  docker start tomato-backend
}

function tomato-backend-shell () {
  mkdir -p "$DIR"/backend/{config,data,logs}
  tomato-write_version_info "$DIR"/backend/config
  docker run -it --rm -v "$TOMATODIR"/backend:/code -v "$TOMATODIR"/shared:/shared \
             -v "$DIR"/backend/config:/config -v "$DIR"/backend/data:/data -v "$DIR"/backend/logs:/logs \
             --link mongodb:db -p 8006:8006 -p 8000:8000 -p 8001:8001 -p 8002:8002 \
             -p 8010:8010 -p 8011:8011 -p 8012:8012 -p 8013:8013 -p 8014:8014 -p 8015:8015 \
             -p 8016:8016 -p 8017:8017 -p 8018:8018 -p 8019:8019 -p 8020:8020 \
             --dns 131.246.9.116 -e "TIMEZONE=Europe/Berlin" tomato-backend /bin/bash
}

function tomato-backend-stop () {
  docker stop tomato-backend
  docker rm tomato-backend
  tomato-delete_version_info "$DIR"/backend/config
}

function tomato-backend-restart() {
  tomato-web-stop
  tomato-backend-stop
  tomato-backend-start
  tomato-web-start
}


function tomato-web-start () {
  mkdir -p "$DIR"/web/config
  tomato-write_version_info "$DIR"/web/config
  SECRET_KEY=$(cat /dev/urandom | tr -cd 'a-zA-Z0-9' | head -c 32)
  docker run -d -v "$TOMATODIR"/web:/code -v "$TOMATODIR"/shared:/shared -v "$DIR"/web/config:/config \
             --link tomato-backend:backend -p 8080:80 --dns 131.246.9.116 --name tomato-web \
             -e "SECRET_KEY=$SECRET_KEY" -e "TIMEZONE=Europe/Berlin" tomato-web
  docker start tomato-web
}

function tomato-web-stop () {
  docker stop tomato-web
  docker rm tomato-web
  tomato-delete_version_info "$DIR"/web/config
}

function tomato-web-restart() {
  tomato-web-stop
  tomato-web-start
}


function tomato-start () {
  tomato-db-start
  tomato-backend-start
  tomato-web-start
}

function tomato-stop () {
  tomato-web-stop
  tomato-backend-stop
  tomato-db-stop
}

function tomato-restart() {
  tomato-stop
  tomato-start
}

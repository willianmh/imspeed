#!/bin/bash

DIR=$1

OFFSET=313967580

if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
    echo "Usage: $0 <directory>" >&2
    exit 1
fi

for file in "$DIR"/*
do
    # macOS uses stat -f, GNU uses stat -c; try both.
    FILE_EPOCH=$(stat -f %B "$file" 2>/dev/null)
    if [ -z "$FILE_EPOCH" ]; then
        FILE_EPOCH=$(stat -c %Y "$file" 2>/dev/null)
    fi

    if [ -z "$FILE_EPOCH" ]; then
        echo "Skipping: $file (cannot read timestamp)" >&2
        continue
    fi

    NEW_EPOCH=$((FILE_EPOCH + OFFSET))

    FORMATTED=$(date -d "@$NEW_EPOCH" +"%Y%m%d%H%M.%S" 2>/dev/null)
    if [ -z "$FORMATTED" ]; then
        FORMATTED=$(date -r "$NEW_EPOCH" +"%Y%m%d%H%M.%S")
    fi

    echo "file: $file -> $FORMATTED"
    touch -mt $FORMATTED $file
done

NEW_DATES=(
"13/12/2025 11:36:12+0100"
"13/12/2025 11:36:18+0100"
"13/12/2025 11:42:53+0100"
"13/12/2025 11:53:21+0100"
"13/12/2025 11:58:48+0100"
"13/12/2025 13:51:31+0100"
"13/12/2025 14:39:59+0100"
"13/12/2025 17:07:29+0100"
"13/12/2025 14:49:26+0100"
"14/12/2025 18:13:58+0100"
"14/12/2025 11:05:10+0100"
"14/12/2025 15:02:28+0100"
"15/12/2025 10:04:58+0100"
"15/12/2025 10:14:23+0100"
"15/12/2025 10:15:31+0100"
"15/12/2025 10:26:16+0100"
"15/12/2025 13:42:02+0100"
"15/12/2025 13:56:03+0100"
"15/12/2025 14:31:55+0100"
"15/12/2025 14:54:03+0100"
)


OFFSET=313967580
for file in "$DIR"/*
do
    # macOS uses stat -f, GNU uses stat -c; try both.
    FILE_EPOCH=$(stat -f %m "$file" 2>/dev/null)
    if [ -z "$FILE_EPOCH" ]; then
        FILE_EPOCH=$(stat -c %Y "$file" 2>/dev/null)
    fi

    if [ -z "$FILE_EPOCH" ]; then
        echo "Skipping: $file (cannot read timestamp)" >&2
        continue
    fi

    NEW_EPOCH=$((FILE_EPOCH + OFFSET))

    FORMATTED=$(date -d "@$NEW_EPOCH" +"%d/%m/%Y %H:%M:%S%:z" 2>/dev/null)
    if [ -z "$FORMATTED" ]; then
        FORMATTED=$(date -r "$NEW_EPOCH" +"%d/%m/%Y %H:%M:%S%z")
    fi

    echo $FORMATTED
done




    # format the new_dates[i] to [[CC]YY]MMDDhhmm[.SS] for touch -t
    INPUT_DATE="${NEW_DATES[$i]}"
    if [ -z "$INPUT_DATE" ]; then
        echo "Skipping: $file (no mapped date)" >&2
        i=$((i + 1))
        continue
    fi

    FORMATTED=$(date -d "$INPUT_DATE" +"%Y%m%d%H%M.%S" 2>/dev/null)
    if [ -z "$FORMATTED" ]; then
        FORMATTED=$(date -j -f "%d/%m/%Y %H:%M:%S%z" "$INPUT_DATE" +"%Y%m%d%H%M.%S" 2>/dev/null)
    fi

    if [ -z "$FORMATTED" ]; then
        echo "Skipping: $file (cannot parse date: $INPUT_DATE)" >&2
        i=$((i + 1))
        continue
    fi

    echo "file: $file -> $FORMATTED"
    touch -mt $FORMATTED $file
    i=$((i + 1))
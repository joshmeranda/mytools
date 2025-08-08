#!/usr/bin/env bash

if [ $# -eq 0 ]; then
    echo "expected files but found none"
    exit 1
fi

while :; do
    case "$1" in
        '-p' | '--prefix' )
            if [ $# -lt 2 ]; then
                echo "expected prefix but found none"
                exit 1
            fi

            prefix="$2";
            shift
            ;;

        '-s' | '--suffix' )
            if [ $# -lt 2 ]; then
                echo "expected suffix but found none"
                exit 1
            fi

            suffix="$2"
            shift
            ;;

        * ) break ;;
    esac

    shift
done

if [ -z "$prefix" ] && [ -z "$suffix" ]; then
    prefix="~"
fi

for path in "$@"; do
    cp --recursive "$path" "$(dirname $path)/$prefix$(basename $path)$suffix"
done

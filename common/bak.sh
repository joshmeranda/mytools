#!/usr/bin/env bash

prefix="~"

while :; do
    case "$1" in
        '-p' | '--prefix' )
            prefix="$2";
            shift
            ;;

        '-s' | '--suffix' )
            suffix="$2"
            shift
            ;;

        * ) break ;;
    esac

    shift
done

for path in "$@"; do
    cp --recursive "$path" "${prefix}${path}${suffix}"
done

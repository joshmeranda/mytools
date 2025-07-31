#!/bin/env bash
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Drain the contents of a directory into the current directory, or one  #
# specified.                                                            #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SCRIPT_NAME="$(basename "$0")"

usage() {
echo "Usage: $SCRIPT_NAME SOURCE... DEST"
}

echo_err() {
    echo -e "$SCRIPT_NAME: $1" 2>&1
}

if [ "$1" == "--help" ]; then usage; exit 1; fi

if [ "$#" -lt 2 ]; then
    echo_err "missing operands."
    usage
    exit 1;
fi

sources=("$@")
dest="${sources[-1]}"

unset 'sources[${#sources[@]} - 1]'

find "${sources[@]}" -mindepth 1 -maxdepth 1 -ignore_readdir_race -exec \
    mv --verbose --target-directory "$dest" '{}' +

rmdir --verbose "${sources[@]}"

#!/bin/env bash
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Drain the contents of a directory into the current directory, or one  #
# specified.                                                            #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SCRIPT_NAME="$(basename "$0")"

usage() {
    echo "Usage: $SCRIPT_NAM SRC DST"
}

if [ "$1" == "--help" ]; then
    usage
    exit 1
fi


case $# in
    0 )
        echo "missing SRC and DST args"
        exit 1
        ;;

    1 )
        echo "missing DST arg"
        exit 1
        ;;

    2 )
        src="$1"
        dst="$2"
        ;;

    * )
        echo "found too many args"
        exit 1
        ;;
esac

if [ "$src" = "$dst" ]; then
    echo "cannot drain '$src' into itself"
    exit 1
fi

targets="$(find "$src" -mindepth 1 -maxdepth 1 -ignore_readdir_race)"

for t in $targets; do
    if [ -e "$dst/$(basename $t)" ]; then
        echo "SRC and DST have a conflict '$(basename $t)'"
        exit 1
    fi
done

mv --verbose --target-directory "$dst" $targets
rmdir --verbose "$src"

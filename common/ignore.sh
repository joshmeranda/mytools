#!/usr/bin/env bash
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Merge the content of one or more gitignore files from the upstream standard  #
# gitignore repository: github.com/github/gitignore                            #
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SCRIPT_NAME="$(basename "$0")"
upstream_url='https://github.com/github/gitignore'

# the directory where the gitignore repository to use was cloned
GITIGNORE_REPO_ROOT=${GITIGNORE_REPO_ROOT:-"$HOME/.local/share"}
GITIGNORE_PATH=${GITIGNORE_PATH:-"$(realpath .)/.gitignore"}

# the directory of the cloned repo
gitignore_repo="$GITIGNORE_REPO_ROOT/gitignore"

function usage {
echo "Usage: $SCRIPT_NAME [list | target...]

  target    a list of target gitignores to be included (case insensitive)
  list      request a list off supported gitignores
  update    pull any changes made to the upstream repo into the local clone, or
            clone upstream if no local repository found
  help      show this help text

For a complete list of all available targets please view the upstream repository here:
    $upstream_url"
}

function echo_err {
    echo -e "$SCRIPT_NAME: $1" 2>&1
}

function update() {
    if [ ! -d "$gitignore_repo" ]; then
        echo "no ignore repository found, cloning from '$upstream_url'"
        git clone "$upstream_url" "$gitignore_repo"
    else
        cd "$gitignore_repo"
        git pull
        cd -
    fi
}

if [ "$#" -eq 0 ]; then
    echo_err "missing operands."
    usage
    exit 1
elif [ "$1" == "help" ]; then
    usage
    exit
fi

case "$1" in
    "target" )
        shift
        ;;
    "list" )
        find "$gitignore_repo" -name '*.gitignore' -exec basename --suffix .gitignore --multiple '{}' +
        exit
        ;;
    "update" )
        update
        exit
        ;;
    "help" )
        usage
        exit
        ;;
    * )
        echo_err 'unknown ignore command'
        exit 2
        ;;
esac

if [ $# -eq 0 ]; then
    echo 'expected at least 1 target but found none'
    exit 1
fi

if ! [ -d "$gitignore_repo" ]; then
    echo "no gitignores found at '$gitignore_repo'"
    ls $gitignore_repo
    exit 1
fi

if [ -f "$GITIGNORE_PATH" ]; then
    echo "cannot create gitignore '$GITIGNORE_PATH', file exists"
    exit 1
fi

for target in "$@"; do
    ignore_file="$(find $gitignore_repo -iname $target.gitignore)"

    if [ -z "$ignore_file" ]; then
        echo "no gitignore for target '$target'"
        exit 1
    fi

    ignore_files+=("$ignore_file")
done

ignore_files="$(sort <<< "${ignore_files[@]}")"

echo "# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This gitignore was auto-generated using the standard templates published by  #
# github here: github.com/github/gitignore                                     #
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #" > $GITIGNORE_PATH

for target in $ignore_files; do
    echo >> $GITIGNORE_PATH  # add some whitespace

    echo "## $(basename $target)" >> $GITIGNORE_PATH
    cat $target >> $GITIGNORE_PATH
done

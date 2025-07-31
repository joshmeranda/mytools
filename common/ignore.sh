#!/usr/bin/env bash
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Merge the content of one or more gitignore files from the upstream standard  #
# gitignore repository: github.com/github/gitignore                            #
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SCRIPT_NAME="$(basename "$0")"
upstream_url='https://github.com/github/gitignore'

# the directory where the gitignore repository to use was cloned
gitignore_dir="$HOME/.local/share"

# the directory of the cloned repo
gitignore_repo="$gitignore_dir/gitignore"

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
        echo "[info] no ignore repository found, cloning from '$upstream_url'"
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

# generate find predicates
pattern=()
for name in "$@"; do
    predicates+=(-iname $name.gitignore -o)
done

predicates+=(-false) # necessary for trailinty '-o'

# write gitignore file
gitignore="$(realpath .)/.gitignore"

echo "# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This gitignore was auto-generated using the standard templates published by  #
# github here: github.com/github/gitignore                                     #
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
" > $gitignore

for target in $(find $gitignore_repo ${predicates[@]}); do
    echo "## $(basename $target)" >> $gitignore
    cat $target >> $gitignore
    echo >> $gitignore  # add some whitespace
done

#!/usr/bin/bash

usage() {
	echo "Usage: $(basename $0) <command> [args]

Commands:
    tags  parse a local VERSION.md for release branches and determine the most recent tags for each branch. All
          operations are done locally so ensure you have up-to-date local branches and tags (git pull && git fetch
          --tags).
"
}

# Utility function to simplify running operations on each release branch. Expects $1 to be a command to call with the name of the release branch as an argument.
for_each_release_branch() {
	if [ ! -f VERSION.md ]
	then
		echo 'Error: No such file VERSION.md found'
		exit 1
	fi

	for branch in $(cat VERSION.md | grep '|' | cut --delimiter '|' --fields 2 | tail +3)
	do
		$1 $branch
	done
}

display_branch_tag() {
	local branch=$1

	if git show-ref --quiet "refs/heads/$branch"
	then
		local tag=$(git describe --tags --abbrev=0 --always $branch)
	else
		local tag='branch not locally found'
	fi

	printf '%-15s%s\n' $branch "$tag"
}

tags() {
	while [ $# -gt 0 ]
	do
		case $1 in
			--help | -h )
				echo "Usage: $(basename $0) tags [repo_dir]"
				exit
				;;
			* )
				if [ -z "$repo_dir" ]
				then
					local repo_dir="$1"
				else
					echo "=== '$repo_dir' ==="
					echo "Error: received too many arguments, expected only 1"
					exit 1
				fi
				;;
		esac

		shift
	done

	if [ -n "$repo_dir" ]
	then
		pushd "$repo_dir" &> /dev/null
	fi

	local current_branch=$(git rev-parse --abbrev-ref HEAD)
	if [ "$current_branch" != "main" ]
	then
		echo "warning: current branch $current_branch != main, results may not be accurate"
	fi

	printf '%-15s%s\n' BRANCH 'CURRENT TAG'
	for_each_release_branch display_branch_tag

	if [ -n "$repo_dir" ]
	then
		popd "$repo_dir" &> /dev/null
	fi
}

while [ $# -gt 0 ]
do
	case $1 in
		--help | -h )
			usage
			exit
			;;
		* )
			cmd="$1"
			shift
			break
			;;
	esac

	shift
done

if [ -z "$cmd" ]
then
	echo 'Error: expected a subcommand but found none'
	exit 1
fi

case "$cmd" in
	tags )
		tags $*
		;;
	* )
		echo "Error: encountered unknown command '$cmd'"
		exit 1
		;;
esac
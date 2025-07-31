#!/usr/bin/bash
# Script for managing local github repositories. Repos are cloned to the path <root>/<owner>/<name>.

CONFIG="${CONFIG:="$HOME/.repomanager"}"

if [ -f "$CONFIG" ]; then
	. "$CONFIG"
fi

GITHUB_REGISTRY=${GITHUB_REGISTRY:-github.com}
SSH_USER=${SSH_USER:-git}
REPO_ROOT=${REPO_ROOT:="$HOME/workspaces"}
CLEAN_AFTER=${CLEAN_AFTER:-28}

show_config() {
	echo "GITHUB_REGISTRY: $GITHUB_REGISTRY
SSH_USER:        $SSH_USER
REPO_ROOT:       $REPO_ROOT"
}

# for_each_repo is an iterato over each repository managed by this script. Expects an argument containing a command to
# be run. The command will be passed the repo dir ($1), the owner ($2), and the repo name ($3).
#
# If a directory under REPO_ROOT does not contain a '.git' repo it will be ignored.
for_each_repo() {
	local owner_dir
	local repo_dir

	for owner_dir in $REPO_ROOT/*; do
		for repo_dir in $owner_dir/*; do
			if ! [ -d "$repo_dir/.git" ]; then
				continue
			fi

			$1 $repo_dir "$(basename $owner_dir)" "$(basename $repo_dir)"
		done
	done
}

clone() {
	local https=true
	local ssh=false

	while [[ $# -gt 0 ]]; do
		case "$1" in
			--https )
				https=true
				ssh=false

				shift
				;;

			--ssh )
				https=false
				ssh=true

				shift
				;;

			--help | -h )
				echo "$(basename $0) [-h] clone <url> | <owner> <repo>

Clone a github repo. The repo will be cloned into the REPO_ROOT directory at the path <owner>/<repo>.

Args:
	--help, -h  Show this help text.
				"
				exit
				;;

			* )
				break
				;;
		esac
	done

	local clone_url
	local owner
	local repo

	case "$#" in
		0 )
			echo "expected args but found none"
			exit 1
			;;
		1 )
			clone_url="$1"

			if [[ "$clone_url" =~ https://.* ]]; then
				repo="$(basename $clone_url .git)"
				owner="$(basename $clone_url $repo.git)"
			elif [[ "$clone_url" =~ .*@*:.*/.*\.git ]]; then
				repo="$(basename $clone_url .git)"
				owner="$(cut -d : -f 1 <<< "${clone_url%/$repo.git}")"
			else
				echo "could not detect owner and repo from url"
				exit
			fi
			
			;;
		
		2 )
			owner=$1
			repo=$2

			if $https; then
				clone_url="https://$GITHUB_REGISTRY/$owner/$repo.git"
			elif $ssh; then
				clone_url="$SSH_USER@$GITHUB_REGISTRY:$owner/$repo.git"
			else
				echo "could not detect clone protocol"
			fi
			;;
		
		* )
			echo "found more args than expected"
			exit 1
			;;
	esac

	local clone_dir="$REPO_ROOT/$owner/$repo"

	git clone "$clone_url" "$clone_dir"
}

clean() {
	local owner_dir
	local repo_dir
	local force=false
	local after=$CLEAN_AFTER

	while [ $# -gt 0 ]; do
		case $1 in
			--force | -f )
				force=true
				;;
			
			--after | -a )
				if [ $# -lt 2 ]; then
					echo "Expected value for '$1' but found none"
					exit 1
				fi

				if ! printf '%d' $2 &> /dev/null; then
					echo "'$1' expected a number but found '$2'"
					exit 1
				fi

				after="$2"
				shift
				;;

			--help | -h )
				echo "$0 clean [-h] -f]

Clean up your repositories

Args:
  --after, -a N  Clean repos after N many days without any modification 
  --force, -f    Do not ask for confirmation before deleting repositories unless there are unstaged changes.
  --help, -h     Show this help text."
				exit 1
				;;
		esac

		shift
	done

	clean_each() {
		local repo_dir="$1"
		local owner="$2"
		local repo="$3"

		local answer=""

		if [ -z "$(find $repo_dir -mtime "-$after")" ]; then
			if $force; then
				answer=Y
			fi

			until [[ $answer =~ [ynYN] ]]; do
				read -n 1 -p "delete '$repo_dir'? [N|y]" answer

				if [ -z $answer ]; then
					answer=N
				fi

				echo $answer
			done

			if [[ $answer =~ [yY] ]]; then
				pushd "$repo_dir"
				if [ -z "$(git status --porcelain)" ]; then
					popd
					continue
				fi
				popd

				rm --recursive --force "$repo_dir"
			fi

			answer=""
		fi

		if [ -z "$(ls -A $(dirname $1))" ]; then
			rm --recursive --force "$owner_dir"
		fi
	}

	for_each_repo clean_each
}

list() {
	local column_length=35
	local url_column_length=50
	local format_str="%-${column_length}s%-${url_column_length}s%-${url_column_length}s\n"

	printf "$format_str" owner/repo origin upstream

	local origin
	local upstream

	list_each() {
		pushd $repo_dir &> /dev/null

		origin="$(git remote get-url origin 2> /dev/null)"
		if [ $? -ne 0 ]; then
			origin=""
		fi

		upstream="$(git remote get-url upstream 2> /dev/null)"
		if [ $? -ne 0 ]; then
			upstream=""
		fi

		printf "$format_str" "$(basename $owner_dir)/$(basename $repo_dir)" $origin $upstream

		popd &> /dev/null
	}

	for_each_repo list_each
}

while [ $# -gt 0 ]; do
	case "$1" in
		clone )
			shift
			clone $*
			break
			;;

		clean )
			shift
			clean $*
			break
			;;
		
		list )
			shift
			list
			break
			;;

		--show-config | -s )
			show_config
			;;

		--help | -h )
			echo "$0: [-h]

Manage your local github repositories.

Commands:
	clone        Clone github repositories into REPO_ROOT.

Args:
    --show-config, -s  Show the script config values. If provided with a command, values will be printed before command runs. If not command, the values will be printed before exiting.
	--help, -h         Show this help text.
"
			exit 1
			;;

		* )
			echo "Unrecognized command or argument '$1', see '$0 --help' for more information"
			exit 1
			;;
	esac

	shift
done
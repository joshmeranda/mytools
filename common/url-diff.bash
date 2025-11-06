#!/usr/bin/bash

CACHE_DIR=${CACHE_DIR:="$HOME/.cache/url-diff"}

# cache_add will check for an existing cache entry, and if none exists create a
# new one. Each entry is a directory containing the cached data and a file will
# additional wget options.
cache_add() {
	while [ $# -gt 0 ]; do
		case "$1" in
			-h | --help )
				echo "Usage: $(basename $0) add <url>

Add a url to the cache

Options:
  -w, --wget <opts>  Pass additional flags to wget as a single string literal."
					  exit
				;;
			-w | --wget )
				wget_opts="$2"
				shift
				;;
			* )
				break
				;;
		esac
		shift
	done

	local url="$1"

	if [ -z "$url" ]; then
		echo "Error: expected url but found none"
		exit 1
	fi

	local cache_path="$CACHE_DIR/$(base64 <<< "$url")"

	if [ -e "$cache_path" ]; then
		echo "Error: cache for '$url' already exists"
		exit 1
	fi

	mkdir --parents "$cache_path"

	if [ "$wget_opts" ]; then
		echo "$wget_opts" > $cache_path/wget
	fi

	wget $wget_opts -o "$cache_path/data" $url
}

cache_remove() {
	while [ $# -gt 0 ]; do
		case "$1" in
			-h | --help )
				echo "Usage: $(basename $0) remove <url>

Remove a url form the cache. If the url is not in the cache, script will exit with a non-zero return code"
				exit
				;;
			* )
				break
				;;
		esac
		shift
	done

	local url="$1"

	if [ -z "$url" ]; then
		echo -e "Error: expected url but found none"
		exit 1
	fi

	local cache_path="$CACHE_DIR/$(base64 <<< $url)"

	if [ ! -e "$cache_path" ]; then
		echo "Error: no cache entry found for '$url'"
		exit 1
	else
		rm --recursive "$cache_path"
	fi
}

cache_list() {
	find "$CACHE_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename '{}' +  | base64 --decode | sort
}

cache_check() {
	while [ $# -gt 0 ]; do
		case "$1" in
			-h | --help )
				echo "Usage: $(basename $0) check <url>

Check a url against a stored cache."
				exit
				;;
			* )
				;;
		esac
		shift
	done

	local url="$1"

	if [ -z "$url" ]; then
		echo "Error: no cache entry found for '$url'"
		exit 1
	fi

	local cache_path="$CACHE_DIR/$(base64 <<< "$url")"

	if [ -e "$cache_path/wget" ]; then
		wget_opts="$(cat "$cache_path/wget")"	
	fi

	wget $wget_opts -o "$cache_path/data.tmp" "$url"

	diff "$cache_path/data" "$cache_path/data.tmp"

	rm "$cache_path/data.tmp"
}

while [ $# -gt 0 ]; do
	case "$1" in
		-h | --help )
			echo "Usage: $(basename $0) <url>

Commands:
  add         Add an antry to the cache.
  remove      Remove an entry from the cache.
  list        List existing cache entries.
  check       Check a url against the cache for changes.

Opts:
  -h, --help  Show this help text

EnvVars:
  CACHE_DIR   The directory to look at for cache operations."
			break
			;;

		add )
			shift
			cache_add $*
			break
			;;

		remove )
			shift
			cache_remove $*
			break
			;;

		list )
			cache_list
			break
			;;

		check )
			shift
			check $*
			break
			;;
		* )
			echo "Error: unexpected argument '$1'"
			exit 1
			;;
	esac

	shift
done
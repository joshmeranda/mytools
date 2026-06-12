#!/usr/bin/bash

while [ "$#" -gt 0 ]; do
	case "$1" in
		-n | --namespace )
			flags+=" --namespace $2"
			shift
			;;

		-A | --all-namespaces )
			flags+=' --all-namespaces'
			;;

		--field-selector )
			if [ $# -lt 1 ]; then
				echo "expected arg to '$1' but found none..."
				eit 1
			fi

			flags+=" --field-selector $2"
			shift
			;;

		-f | --filename )
			if [ $# -lt 1 ]; then
				echo "expected arg to '$1' but found none..."
				exit 1
			fi

			flags+=" --filename $2"
			shift
			;;

		-R | --recursive )
			if [ $# -lt 1 ]; then
				echo "exepcted arg to '$1' but found none..."
				exit 1
			fi

			flags+=" --recursive $2"
			shift
			;;

		--raw )
			if [ $# -lt 1 ]; then
				echo "exepcted arg to '$1' but found none..."
				exit 1
			fi

			flags+=" --raw $2"
			shift
			;;

		-l | --selector )
			if [ $# -lt 1 ]; then
				echo "expected arg to '$1' but found none..."
				exit 1
			fi

			flags+=" --selector $2"
			shift
			;;
		
		* )
			if [ -z "$callback" ]; then
				callback="$1"
			elif [ -z "$kind" ]; then
				kind="$1"
			elif [ -z "$name" ]; then
				name="$1"
			else
				printf 'encountered unexpected argument %s' "$1"
				exit 1
			fi
			;;
	esac

	shift
done

if [ -z "$callback" ]; then
	echo 'expected at least 1 argument but found none'
	exit 1
elif [ -z "$kind" ]; then
	echo 'expected at least 2 arguments but found 1'
	exit 1
fi

lock_file=.lock

trap "rm --force $lock_file" EXIT

kubectl get --watch --output jsonpath='{@}{"\n"}' $flags $kind $name |
while IFS= read -r obj; do
	flock .lock $callback "$obj"
done

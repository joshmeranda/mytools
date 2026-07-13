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

		-h | --help)
			echo "$(basename $0): [-n <namespace>] [-A] [--field-selector <field selector>]
                 [-f <path>] [-R <true|false>] [--raw <uri>] [-l <selector>]
                 <SCRIPT> <KIND> [NAME]
			
$(basename $0) allows you to run k8s controllers straight from the terminal or
in your scripts. For example, to run the SCRIPT at './update-tracker.bash' each
time a pod is updated run:
	$(basename $0) ./update-tracker.bash pod

For each update a new instance of SCRIPT is started, but will wait until the
previous instance is complete. Be warned that this may eat up computing
resources if there are many triggering events. To help prevent this run your
own checks and validations early.

For more information on the flags specifiec above see 'kubectl get --help'.

Note: No attempt is made to limit what events will be received by the callback
      script. If you receive an event for a resource and send an update
      to that same resource, you will receive another event for that update."
			exit
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

lock_file=.lock-$BASHPID

trap "rm --force $lock_file" EXIT

kubectl get --watch --output jsonpath='{@}{"\n"}' $flags $kind $name |
while IFS= read -r obj; do
	flock $lock_file $callback "$obj" &
done

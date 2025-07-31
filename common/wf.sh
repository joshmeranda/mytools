#!/usr/bin/env sh

# todo: support inverting the condition or provide more condition options

usage="Usage: $(basename "$0") [-hq] [-m <max-attempts>] [-i <interval>]
																		 [-o <never|last|last-err|all>] <args>...

opts:
	-m <max-attempts>     maximum count amount [inf]
	-i <interval>         the interval between attempts [1]
	-o <never|last|all>   control whether out output to the given command is
												displayed never, only the last attempt, or all attempts
												[last]
	-p                    print a '.' each time the command is tried and whether
												the command succeeded or failed on the last attempt
"

if [ "$#" -eq 0 ]; then
	echo "expected a command but found none"
	echo "$usage"
	exit 1
fi

assert_positive_int()
{
	case "$1" in
		*[!0-9]*|'')
			echo "value '$1' is not a valid positive"
			exit 1
			;;
	esac
}

max_attempts=-1
interval=1
output_level=last
progress=false

while [ "$#" -gt 0 ]; do
	case "$1" in
		-h)
			echo "$usage"
			exit
			;;
		-m)
			assert_positive_int "$2"
			max_attempts=$2
			shift
			;;
		-i)
			assert_positive_int "$2"
			interval=$2
			shift
			;;
		-o)
			output_level="$2"

			case "$output_level" in
				never|last|last-err|all) ;;
				*)
					echo "'$output_level' is not a valid option to '-o'"
					echo "$usage"
					;;
			esac

			shift
			;;
		-p)
			progress=true
			;;
		*)
			args="$*"
			break
			;;
	esac
	shift
done

if [ "$output_level" = never ]; then
	cmd_out=/dev/null
else
	cmd_out="$(mktemp --suffix .wf)"
fi

attempts=0

while ! $args > "$cmd_out" 2>&1 && { [ "$max_attempts" = -1 ] || [ "$attempts" -lt "$max_attempts" ]; }; do
	attempts=$((attempts + 1))

	if [ "$output_level" = always ]; then
		cat "$cmd_out"
	elif $progress; then
		printf .
	fi

	sleep "$interval"
done

if $progress; then
	if [ "$attempts" -eq "$max_attempts" ]; then
		echo err
	else
		echo ok
	fi
fi

if [ "$output_level" = last ]; then
	cat "$cmd_out"
elif [ "$output_level" = last-err ] && [ "$attempts" -eq "$max_attempts" ]; then
	cat "$cmd_out"
fi

if [ "$attempts" -eq "$max_attempts" ]; then
	exit 1
fi

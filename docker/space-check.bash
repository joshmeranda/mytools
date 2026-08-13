#!/usr/bin/bash

usage="Usage: $(basename $0) SIZE

SIZE is the amount of space you want docker to use. Size is expected to be a
whole number in GB. If the GB unit is ommited, the command will exit with
non-zero code (ex. 10GB is acceptable but neither 10.1GB or 10 is).

Args:
  -n, --notify    Rather tha printing message to commaned line send a system
                  notification instead using notify-send
  -h, --help      Show this help text"

notify=false

while [ $# -gt 0 ]
do
	case $1 in
		-n | --notify )
			notify=true
			;;
		-h | --help )
			echo "$usage"
			exit
			;;
		* )
			break
			;;
	esac

	shift
done

case $# in
	0 )
		printf "Error: expected 1 arg but found %d\n%s\n" $# "$usage"
		exit 1
		;;
	1 )
		max_size=$1

		if [[ "$1"  =~ [0-9]+GB ]]
		then
			max_size=$1
		else
			printf "Error: could not understand given size '%s'\n%s\n" $max_size "$usage"
			exit 1
		fi
		;;
	* )
		printf "Error: expected only 1 arg but found %d\n%s" $# "$usage"
		exit 1
		;;
esac

B_TO_GB=1000000000
B_TO_MB=1000000
B_TO_KB=1000

from_GB_to_B() {
	bc <<< "$1 * $B_TO_GB / 1"
}

from_MB_to_B() {
	bc <<< "$1 * $B_TO_MB / 1"
}

from_KB_to_B() {
	bc <<< "$1 * $B_TO_KB / 1"
}

to_B() {
	size=${1%??}

	# Since we are ignoring case here we are doing a "gainy" transormation
	# which may lead to false positives on total docker disk usage exceeding
	# configured maximums.
	unit=$(echo ${1: -2} | tr '[[:lower:]]' '[[:upper:]]')

	case $unit in
		GB | MG | KB )
			from_${unit}_to_B $size
			;;
		* )
			echo ${1%?}
			;;
	esac
}

max_size_b=$(to_B $max_size)
total_size=0

for i in $(docker system df --format '{{.Size}}')
do
	size=$(to_B $i)
	((total_size+=size))
done

if [ $total_size -gt $max_size_b ]
then
	delta=$((total_size - max_size_b))

	if [ $(bc <<< "$delta >= $B_TO_GB") -eq 1 ]
	then
		delta=$(bc <<< "scale=2; $delta / $B_TO_GB")GB
	elif [ $(bc <<< "$delta >= $B_TO_MB") -eq 1 ]
	then
		delta=$(bc <<< "scale=2; $delta / $B_TO_MB")MB
	elif [ $(bc <<< "$delta >= $B_TO_KB") -eq 1 ]
	then
		delta=$(bc <<< "scale=2; $delta / $B_TO_KB")KB
	else
		delta=${delta}B
	fi

	message="Docker storage maximum ($max_size) exceeded by $delta"
fi

if $notify
then
	notify-send --urgency=normal "$message"
else
	echo $message
fi
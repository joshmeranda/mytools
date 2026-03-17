#!/usr/bin/bash

while [ $# -gt 0 ]
do
	case "$1" in
		*)
			packages="$packages $1"
		;;
	esac
	shift
done

for pkg in $packages
do
	go get $pkg

	git add go.mod go.sum
	git commit -m "go get $pkg"
done

go mod tidy
git add go.mod go.sum
git commit -m 'go mod tidy'

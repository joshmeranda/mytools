#!/usr/bin/bash

# https://github.com/rancherlabs/rancher-process/blob/main/docs/teams/frameworks/RELEASE.md

releases_per_page=50

function check_repo_version() {
	local repo=$1
	local version=$2
	local minor_version="$(cut --delimiter . --fields 1,2 <<< $version)"

	current_release_time="$(gh api /repos/$repo/releases/tags/$version | jq '.created_at | fromdateiso8601')"
	# ((current_release_time-=1000000))

	# might need to sort these
	newer_versions="$(
		gh api "/repos/$repo/releases?per_page=$releases_per_page" |
			jq --raw-output ".[] |
				select ( .created_at | fromdateiso8601 > $current_release_time ) |
				select (.tag_name | startswith(\"$minor_version\")) |	
				.tag_name" |
			tr '\n' ' '
	)"

	webhook_deps="$(grep $repo <<< "$webhook_go_mod" | grep --invert-match '// indirect' | sort)"
	rancher_deps="$(grep $repo <<< "$rancher_go_mod" | grep --invert-match '// indirect' | sort)"

	# todo: only do this for sync_dependencies
	if [ -z "$(diff <(echo "$webhook_deps") <(echo "$rancher_deps"))" ]
	then
		synced="yes"
	else
		synced="no"
		diff <(echo "$webhook_deps") <(echo "$rancher_deps")
	fi

	printf "%-26s %-20s %-10s %s\n" $repo $version "$synced" "$newer_versions"
}

rancher_version=$1

dependencies=(
	rancher/wrangler/v3
	rancher/dynamiclistener
	rancher/lasso
	rancher/remotedialer
	rancher/apiserver
	rancher/norman
	rancher/steve
)

charts=(
	rancher/webhook
	rancher/remotedialer-proxy
)

sync_dependencies=(
	rancher/dynamiclistener
	rancher/lasso
	rancher/wrangler
	rancher/wrangler/v2
	rancher/wrangler/v3
)

if [ -z "$rancher_version" ]
then
	echo "expected at leas 1 arg but found none"
	exit 1
fi

if ! gh api "/repos/rancher/rancher/branches/release/$rancher_version" &> /dev/null; then
	rancher_branch=main
else
	rancher_branch=release/$rancher_version
fi

webhook_branch="$(curl --silent https://raw.githubusercontent.com/rancher/webhook/refs/heads/main/VERSION.md | grep $rancher_version | cut --delimiter '|' --fields 2 | tr --delete ' ')"

rancher_go_mod="$(curl --silent https://raw.githubusercontent.com/rancher/rancher/$rancher_branch/go.mod)"
webhook_go_mod="$(curl --silent https://raw.githubusercontent.com/rancher/webhook/refs/heads/$webhook_branch/go.mod)"

build_yaml="$(curl --silent https://raw.githubusercontent.com/rancher/rancher/$rancher_branch/build.yaml)"

printf "%-26s %-20s %-10s %-s\n" Repository 'Current Release' Synced 'Newer Releases'

for dep in ${dependencies[@]}
do
	dep_version="$(grep --extended-regexp "$dep v" <<< "$rancher_go_mod" | cut --delimiter ' ' --fields 2)"
	check_repo_version $(cut --delimiter '/' --fields 1,2 <<< $dep) $dep_version
done

for chart in ${charts[@]}
do
	# seperate chart name from repo
	# remove '-' for remotedialer-proxy => remoteDialerProxyVersion
	chart_name=$(cut --delimiter '/' --fields 2 <<< $chart | tr  --delete '-')
	chart_version=v$(grep --ignore-case "$chart_name" <<< "$build_yaml" | cut --delimiter :  --fields 2 | cut --delimiter p --fields 2)

	check_repo_version $chart $chart_version
done
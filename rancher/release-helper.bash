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

	printf "%-26s %-20s %s\n" $repo $version "$newer_versions"
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

if [ -z "$rancher_version" ]
then
	echo "expected at leas 1 arg but found none"
	exit 1
fi

if ! gh api "/repos/rancher/rancher/branches/release/$rancher_version" &> /dev/null; then
	branch=main
else
	branch=release/$rancher_version
fi

rancher_go_mod="$(curl --silent https://raw.githubusercontent.com/rancher/rancher/$branch/go.mod)"

build_yaml="$(curl --silent https://raw.githubusercontent.com/rancher/rancher/$branch/build.yaml)"

printf "%-26s %-20s %-s\n" Repository 'Current Release' 'Newer Releases'

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
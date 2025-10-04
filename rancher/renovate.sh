#!/usr/bin/bash

check_pr() {
	local api_pr_url="$1"
	local pr_reviews_url="$api_pr_url/reviews"
	local pr="$(gh api $api_pr_url)"

    reviews="$(gh api $api_pr_url/reviews -q "group_by(.user.login) | .[] | sort_by(.submitted_at | fromdate) | .[-1] | if .user.login != $(jq .user.login <<< $pr) then .user.login + \" \" + .state else empty end")"
	approved=$(grep APPROVED <<< "$reviews" | wc --lines)
	changes_requested=$(grep CHANGES_REQUESTED <<< "$reviews" | wc --lines)

	printf '│ %+50s │ %2d✔ %2d✖ │\n' $(jq --raw-output .html_url <<< $pr) ${approved:-0} ${changes_requested:-0}
}

DAY_RANGE=${DAY_RANGE:-7}
REPOS=${REPOS:-"rancher/steve rancher/wrangler rancher/norman"}

query="created:>=$(date --date "$DAY_RANGE days ago" +%Y-%m-%d) is:pr state:open author:app/renovate-rancher" # repo:rancher/steve repo:rancher/wrangler repo:rancher/norman"

for repo in $REPOS; do
	query="$query repo:$repo"
done

if [ -n "$DEBUG" ]; then
	echo "DAY_RANGE: $DAY_RANGE"
	echo "    REPOS: $REPOS"
	echo "    query: $query"
	DEBUG=''
fi

pr_urls=$(gh api --method GET search/issues --paginate --slurp \
	--raw-field q="$query" \
	| jq -c -M -r '.[].items[].pull_request.url')

printf '┌%s┐\n' $(printf '─%.0s' {0..61})
printf '│ %+50s │ %+7s │\n' 'pull request' reviews
printf '├%s┼%s┤\n' $(printf '─%.0s' {0..51}) $(printf '─%.0s' {0..8})

for pr_url in $pr_urls; do
	check_pr $pr_url &
done
wait

printf '└%s┘\n' $(printf '─%.0s' {0..61})

# │ ├ ─ ┼ ┤ ┌ ┐ └ ┘

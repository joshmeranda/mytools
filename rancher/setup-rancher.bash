#!/usr/bin/env bash
# Script for establishing a local rancher setup using k3d as a driver. When creating a server, the file pointed to by
# your 'KUBECONFIG' envvar will be updated. When creating agents a new KUBECONFIG file will be created with the name
# ./<cluster name>.yaml.

rancher_run_mode=binary

helm_values_flags='--set bootstrapPassword=password12345 --set hostname=rancher.local.com --set rancherImage=joshmeranda/rancher --set rancherImageTag=dev-head'

cluster_prefix=rancher

agents=0

k9s=false

while [[ $# -gt 0 ]]; do
	case "$1" in
		--mode | -m )
			if [ $# -lt 2 ]; then
				echo "expected value after '$1' but found none"
				exit 1
			fi

			case "$2" in
				binary | docker | chart )
				;;

				* )
					echo "unsupported rancher run mode '$2'"
					exit 1
				;;
			esac

			rancher_run_mode="$2"
			shift
			;;

		--chart | -c )
			if [ $# -lt 2 ]; then
				echo "expected value after '$1' but found none"
				exit 1
			fi

			rancher_chart="$2"
			shift
			;;

		--set | -s )
			if [ $# -lt 2 ]; then
				echo "expected value after '$1' but found none"
				exit 1
			fi

			helm_values_flags="$helm_values_flags --set $2"
			shift
			;;

		--prefix | -p )
			if [ $# -lt 2 ]; then
				echo "expected value after '$1' but found none"
				exit 1
			fi

			cluster_prefix="$2"
			shift
			;;

		--agents | -a )
			if [ $# -lt 2 ]; then
				echo "expected value after '$1' but found none"
				exit 1
			fi

			if ! printf '%d' $2 &> /dev/null; then
				echo "agent count must be a number but found '$2'"
				exit 1
			fi

			agents=$2
			shift
			;;

		--image | -i )
			if [ $# -lt 2 ]; then
				echo "expected value after '$1' but found none"
				exit 1
			fi

			k3s_image="$2"
			shift
			;;

		--k9s | -k )
			k9s=true
			;;

		--help | -h )
		echo "$(basename $0): [-m <mode>] [-c <ref>] [-p <prefix>] [-a <agents>] [i <image>] [-k] [-h]

Args
  --mode, -m <str>     The mode rancher is expected to be run as. Can be one of chart, docker, or binary. [$rancher_run_mode]
  --chart, -c <ref>    The reference to the chart to install when mode == \'chart\', see https://v2.helm.sh/docs/helm/#helm-install for more information on chart references
  --set, -s <str>      See https://helm.sh/docs/helm/helm_upgrade for more information on the format for --set
  --prefix, -p <str>   The prefix to use when generating cluster names. [$cluster_prefix]
  --agents, -a  <int>  Specify how many rancher agent clusters to start [$agents]
  --image, -i <image>  The image to use when creating clusters, if not specified the default k3d vlaue is used
  --k9s, -k            Open k9s to follow the new cluster [$k9s]
  --help, -h           Show this help text"
			exit
			;;

		* )
			echo "Unrecognized flag '$1', run '$(basename $0) --help' for more information"
			exit 1
			;;
	esac

	shift
done

echo "Cluster Prefix : $cluster_prefix"
echo "Agent Clusters : $agents"
echo "K9s            : $k9s"
if [ -n "$k3s_image" ]; then
echo "K3S IMAGE      : $k3s_image"
fi
if [ -n "$rancher_chart" ] && [ "$rancher_run_mode" == "chart" ]; then
echo "RANCHER CAHRT  : $rancher_chart"
echo "HELM VALUES    : $helm_values_flags"
fi

new_clusters=()

create_server() {
	if [ "$rancher_run_mode" == "chart" ] ; then
		local args='--port 80:80@loadbalancer --port 443:443@loadbalancer'
	fi

	if [ -n "$k3s_image" ]; then
		args="$args --image $k3s_image"
	fi

	k3d cluster create $args "$cluster_prefix"-server
	kubectl config set-context --current --namespace cattle-system

	new_clusters+=($cluster_prefix-server)
}

create_agent() {
	local id=$1
	local name=$cluster_prefix-agent-$id

	if [ -n "$k3s_image" ]; then
		local args="--image $k3s_image"
	fi

	if k3d cluster get $name &>/dev/null; then
		k3d cluster delete $name
		rm $name.yaml
	fi

	KUBECONFIG=$name.yaml k3d cluster create $args $name
	KUBECONFIG=$name.yaml kubectl config set-context --current --namespace cattle-system

	new_clusters+=($name)
}

if k3d cluster get "$cluster_prefix-server" &>/dev/null; then
	k3d cluster delete "$cluster_prefix-server"
fi

create_server

case "$rancher_run_mode" in
	chart)
		if [ "$(helm search repo jetstack/cert-manager -o json | jq length)" -lt 1 ]; then
			helm repo add --force-update jetstack https://charts.jetstack.io
		fi

		helm upgrade --install --create-namespace --namespace cert-manager --set crds.enabled=true cert-manager jetstack/cert-manager

		if [ -n "$rancher_chart" ]; then
			helm upgrade --install --create-namespace --namespace cattle-system rancher "$rancher_chart" $helm_values_flags
		fi
		;;
	docker | binary)
		;;
	*)
		printf 'unsupported mode "%s", must be one of chart, docker, or binary' "$rancher_run_mode"
		;;
esac

for i in $(seq $agents) ; do
	create_agent $i
done

# todo: list only created clusters
k3d cluster list ${new_clusters[@]}

if $k9s ; then
	echo starting k9s...
	sleep 5
	k9s
fi

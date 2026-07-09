import os
import pytest
import pathlib
import subprocess
from kubernetes import client, config
import typing
import time

_CONTROLLER_K3S_IMAGE: str = "rancher/k3s:v1.36.1-k3s1"
_CONTROLLER_K3D_CLUSTER_CREATE_TIMEOUT: int = 60

_CONTROLLER_PATH: str = os.path.abspath("kubernetes/controller.bash")

_CONTROLLER_TEST_NAMESPACE="testing-namespace"
_CONTROLLER_TEST_VISITED_ANNOTATION = "mytools/visited"


def _is_config_map_visited(config_map: client.V1ConfigMap=None, v1: client.CoreV1Api=None, name: str="") -> bool:
	if config_map == None and v1 != None and name != "":
		config_map: client.V1ConfigMap = v1.read_namespaced_config_map(namespace=_CONTROLLER_TEST_NAMESPACE, name=name)
	elif config_map != None and name != "":
		raise Exception("name and config_map are mutually exclusive")
	elif name != "" and v1 == None:
		raise Exception("when name != \"\" v1 must be specified")

	try:
		return config_map.metadata.annotations["visited"] == "true"
	except:
		return False


def _wait_until(callback: typing.Callable[[], bool], timeout: float=5, interval: float=.5) -> bool:
	end_after = time.time() + timeout

	while time.time() < end_after:
		if callback():
			return True

		time.sleep(interval)
	
	return False


@pytest.fixture(scope="session")
def _kubeconfig(tmpdir_factory: pytest.TempPathFactory) -> pathlib.Path:
	cluster_name = "controller-test"
	kubeconfig= tmpdir_factory.mktemp("kubeconfig").join("kubeconfig")

	# todo: check if k3 is installed (do the same for git)
	proc = subprocess.run(
		args=[
			"/usr/local/bin/k3d", "cluster", "create",
			"--wait",
			"--timeout", str(_CONTROLLER_K3D_CLUSTER_CREATE_TIMEOUT) + "s",
			"--image", _CONTROLLER_K3S_IMAGE,
			cluster_name,
		],
		env={"KUBECONFIG": kubeconfig},
	)
	assert proc.returncode == 0

	yield kubeconfig

	proc = subprocess.run(
		args=["/usr/local/bin/k3d", "cluster", "delete", cluster_name],
	)
	assert proc.returncode == 0


@pytest.fixture(scope="session")
def _k8s_client(_kubeconfig: pathlib.Path) -> client.ApiClient:
	k8s_client = config.new_client_from_config(str(_kubeconfig))

	v1 = client.CoreV1Api(api_client=k8s_client)
	v1.create_namespace({
		"apiVersion": "v1",
		"kind": "Namespace",
		"metadata": {
			"name": _CONTROLLER_TEST_NAMESPACE,
		}
	})
	
	return k8s_client


@pytest.fixture(scope="session")
def _handler(tmpdir_factory: pytest.TempPathFactory) -> pathlib.Path:
	script = tmpdir_factory.mktemp("scripts").join("update_tracker.bash")

	assert not script.exists()

	with open(script, "w") as f:
		f.write('''#!/bin/bash

		  # tr will remove all '"' from the queried value
		  visited=$(jq '.metadata.annotations.visited' <<< "$1" | tr --delete '"')

		  if [ "$visited" != "true" ]
		  then
		    jq '.metadata.annotations.visited="true"' <<< "$1" | kubectl apply -f -
		  fi
		''')
	
	os.chmod(script, 0o700)

	return script


class TestController:
	def test_visit_specific_configmap(self, _k8s_client: client.ApiClient, _kubeconfig: pathlib.Path, _handler: pathlib.Path, request: pytest.FixtureRequest):
		cm_name = f"test-configmap-{request.node.name.replace("_", "-")}"

		with _k8s_client:
			proc = subprocess.Popen(
				args=[
					_CONTROLLER_PATH, str(_handler),
					"configmap", cm_name,
					"--namespace", _CONTROLLER_TEST_NAMESPACE
				],
				env={
					"KUBECONFIG": str(_kubeconfig),
				},
			)

			v1 = client.CoreV1Api(api_client=_k8s_client)

			v1.create_namespaced_config_map(
				namespace=_CONTROLLER_TEST_NAMESPACE,
				body={
					"apiVersion": "v1",
					"kind": "ConfigMap",
					"metadata": {
						"name": cm_name,
						"annotations": {
							_CONTROLLER_TEST_VISITED_ANNOTATION: "false",
						},
					},
				}
			)
			def cleanup_configmap():
				v1.delete_namespaced_config_map(namespace=_CONTROLLER_TEST_NAMESPACE, name=cm_name)
			request.addfinalizer(cleanup_configmap)

			def callback() -> bool:
				return _is_config_map_visited(v1=v1, name=cm_name)

			assert _wait_until(callback)

			proc.kill()
			proc.wait()

	def test_visit_all_configmaps_in_namespace(self, _k8s_client: client.ApiClient, _kubeconfig: pathlib.Path, _handler: pathlib.Path, request: pytest.FixtureRequest):
		with _k8s_client:
			proc = subprocess.Popen(
				args=[
					_CONTROLLER_PATH, str(_handler),
					"configmap",
					"--namespace", _CONTROLLER_TEST_NAMESPACE
				],
				env={
					"KUBECONFIG": str(_kubeconfig),
				},
			)

			v1 = client.CoreV1Api(api_client=_k8s_client)

			for i in range(5):
				v1.create_namespaced_config_map(
					namespace=_CONTROLLER_TEST_NAMESPACE,
					body={
						"apiVersion": "v1",
						"kind": "ConfigMap",
						"metadata": {
							"name":  f"test-configmap-{request.node.name.replace("_", "-")}-{i}",
							"annotations": {
								_CONTROLLER_TEST_VISITED_ANNOTATION: "false",
							},
						},
					}
				)
			v1.create_namespaced_config_map(
				namespace="default",
					body={
						"apiVersion": "v1",
						"kind": "ConfigMap",
						"metadata": {
							"name":  f"ignore-me",
							"annotations": {
								_CONTROLLER_TEST_VISITED_ANNOTATION: "false",
							},
						},
					}
			)

			def cleanup_configmaps():
				v1.delete_namespaced_config_map(namespace="default", name="ignore-me")
				for i in range(5):
					v1.delete_namespaced_config_map(namespace=_CONTROLLER_TEST_NAMESPACE, name=f"test-configmap-{request.node.name.replace("_", "-")}-{i}")
			request.addfinalizer(cleanup_configmaps)
			
			def callback() -> bool:
				configmaps: client.V1ConfigMapList = v1.list_config_map_for_all_namespaces()
				for cm in configmaps.items:
					if cm.metadata.namespace == _CONTROLLER_TEST_NAMESPACE and not _is_config_map_visited(config_map=cm):
						return False
					elif cm.metadata.namespace != _CONTROLLER_TEST_NAMESPACE and _is_config_map_visited(config_map=cm):
						return False
				
				return True
			
			assert _wait_until(callback)

			proc.kill()
			proc.wait()

	def test_visit_all_configmaps_in_cluster(self, _k8s_client: client.ApiClient, _kubeconfig: pathlib.Path, _handler: pathlib.Path, request: pytest.FixtureRequest):
		with _k8s_client:
			proc = subprocess.Popen(
				args=[
					_CONTROLLER_PATH, str(_handler),
					"configmap",
					"--all-namespaces"
				],
				env={
					"KUBECONFIG": str(_kubeconfig),
				},
			)

			v1 = client.CoreV1Api(api_client=_k8s_client)

			for i in range(5):
				v1.create_namespaced_config_map(
					namespace=_CONTROLLER_TEST_NAMESPACE,
					body={
						"apiVersion": "v1",
						"kind": "ConfigMap",
						"metadata": {
							"name":  f"test-configmap-{request.node.name.replace("_", "-")}-{i}",
							"annotations": {
								_CONTROLLER_TEST_VISITED_ANNOTATION: "false",
							},
						},
					}
				)
			v1.create_namespaced_config_map(
				namespace="default",
					body={
						"apiVersion": "v1",
						"kind": "ConfigMap",
						"metadata": {
							"name":  f"ignore-me",
							"annotations": {
								_CONTROLLER_TEST_VISITED_ANNOTATION: "false",
							},
						},
					}
			)

			def cleanup_configmaps():
				v1.delete_namespaced_config_map(namespace="default", name="ignore-me")
				for i in range(5):
					v1.delete_namespaced_config_map(namespace=_CONTROLLER_TEST_NAMESPACE, name=f"test-configmap-{request.node.name.replace("_", "-")}-{i}")
			request.addfinalizer(cleanup_configmaps)
			
			def callback() -> bool:
				print("=== [test_visit_all_configmaps_in_cluster 000] ===")
				for cm in v1.list_config_map_for_all_namespaces().items:
					if not _is_config_map_visited(config_map=cm):
						print(f"=== [test_visit_all_configmaps_in_cluster 001] {cm.metadata.namespace}/{cm.metadata.name} ===")
						return False
				return True
			
			assert _wait_until(callback, timeout=30)

			proc.kill()
			proc.wait()

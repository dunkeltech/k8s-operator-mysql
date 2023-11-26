# This code is licensed under the MIT License.
# See LICENSE.txt for more details.

import base64
import kopf
import logging
import kubernetes.client as k8s
from kubernetes.client.rest import ApiException

import dunkel_tech.k8s.operator.mysql.database # noqa: F401
import dunkel_tech.k8s.operator.mysql.user # noqa: F401
from dunkel_tech.k8s.operator.mysql.utils import generate_random_password

LOG = logging.getLogger(__name__)

@kopf.on.create('dunkel.tech', 'v1', 'mysqloperators')
def create_operators(spec, name, namespace, logger, **kwargs):
    LOG.info(f"Creating MySQLOperator {name} in namespace {namespace}")

    mysql_pvc = dict(
        apiVersion="v1",
        kind="PersistentVolumeClaim",
        metadata=dict(name=f"{name}-mysql-pv-claim"),
        spec=dict(
            storageClassName="",
            accessModes=["ReadWriteOnce"],
            resources=dict(requests=dict(storage="2Gi")),
        ),
    )

    root_password = generate_random_password()
    mysql_deployment = dict(
        apiVersion="apps/v1",
        kind="Deployment",
        metadata=dict(name=f"{name}-mysql"),
        spec=dict(
            selector=dict(matchLabels=dict(app=f"{name}-mysql")),
            template=dict(
                metadata=dict(labels=dict(app=f"{name}-mysql")),
                spec=dict(
                    containers=[
                        dict(
                            name=f"{name}-mysql",
                            image=f"mysql:{spec['mysql_version']}",
                            env=[dict(name="MYSQL_ROOT_PASSWORD", valueFrom=dict(secretKeyRef=dict(name=f"{name}-mysql-root-password", key="password")))],
                            ports=[dict(containerPort=3306, name="mysql")],
                            volumeMounts=[dict(name=f"{name}-mysql-persistent-storage", mountPath="/var/lib/mysql")],
                        )
                    ],
                    volumes=[dict(name=f"{name}-mysql-persistent-storage", persistentVolumeClaim=dict(claimName=f"{name}-mysql-pv-claim"))],
                ),
            ),
        ),
    )

    secret = dict(
        apiVersion="v1",
        kind="Secret",
        metadata=dict(name=f"{name}-mysql-root-password"),
        type="Opaque",
        data=dict(password=base64.b64encode(root_password.encode()).decode()),
    )

    # generate service for mysql
    mysql_service = dict(
        apiVersion="v1",
        kind="Service",
        metadata=dict(name=f"{name}-mysql"),
        spec=dict(
            ports=[dict(port=3306, targetPort=3306)],
            selector=dict(app=f"{name}-mysql"),
        ),
    )

    kopf.adopt(mysql_pvc)
    kopf.adopt(secret)
    kopf.adopt(mysql_deployment)
    kopf.adopt(mysql_service)

    core_api = k8s.CoreV1Api()
    apps_api = k8s.AppsV1Api()
    # deploy = core_api.read_namespaced_service("foo", "bar")
    # cluster_ip = deploy.spec.cluster_ip
    try:
        core_api.create_namespaced_persistent_volume_claim(namespace=namespace, body=mysql_pvc)
        core_api.create_namespaced_secret(namespace=namespace, body=secret)
        apps_api.create_namespaced_deployment(namespace=namespace, body=mysql_deployment)
        core_api.create_namespaced_service(namespace=namespace, body=mysql_service)
    except ApiException as e:
        LOG.error(f"Exception when calling CoreV1Api->create_namespaced_persistent_volume_claim: {e}")
        raise kopf.TemporaryError(f"Failed to create PVC: {e}", delay=5)

@kopf.on.delete('dunkel.tech', 'v1', 'mysqloperators')
def delete_operators(spec, name, namespace, logger, **kwargs):
    LOG.info(f"Deleting MySQLOperator {name} in namespace {namespace}")
    core_api = k8s.CoreV1Api()
    apps_api = k8s.AppsV1Api()

    try:
        # Get all resources of type mysqldatabases
        resource_to_consider = ["mysqldatabases", "mysqlusers"]

        api_instance = k8s.CustomObjectsApi()
        group = "dunkel.tech"
        version = "v1"

        for resource_type in resource_to_consider:
            resources = api_instance.list_namespaced_custom_object(group, version, namespace, resource_type)

            # Process the resources
            for resource in resources["items"]:
                if resource["spec"]["operator"] == name:
                    LOG.debug(f"Deleting {resource_type}.{group}/{version} {resource['metadata']['name']}")
                    api_instance.delete_namespaced_custom_object(group, version, namespace, resource_type, resource['metadata']['name'])

    except ApiException as e:
        LOG.error(f"Exception when calling CoreV1Api->delete_namespaced_deployment: {e}")
        raise kopf.TemporaryError(f"Failed to delete deployment: {e}")

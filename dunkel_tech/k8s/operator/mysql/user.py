# This code is licensed under the MIT License.
# See LICENSE.txt for more details.

import base64
import kopf
import logging
import kubernetes.client as k8s
import mysql.connector as mysql

from kubernetes.client.rest import ApiException

from dunkel_tech.k8s.operator.mysql.utils import create_database_user, generate_random_password, get_k8s_secret

LOG = logging.getLogger(__name__)

@kopf.on.create('dunkel.tech', 'v1', 'mysqlusers')
def create_user(spec, name, namespace, logger, **kwargs):
    LOG.info(f"Creating MySQL User {spec['username']} in namespace {namespace}")
    core_api = k8s.CoreV1Api()

    try:
        deploy = core_api.read_namespaced_service(f"{spec['operator']}-mysql", namespace)
        cluster_ip = deploy.spec.cluster_ip
        LOG.debug("Cluster IP: %s", cluster_ip)
        LOG.debug("Creating database %s", name)
        user_pw = generate_random_password()

        secret = dict(
            apiVersion="v1",
            kind="Secret",
            metadata=dict(name=f"{spec['operator']}-mysql-{name}"),
            type="Opaque",
            data=dict(
                user=base64.b64encode(spec["username"].encode()).decode(),
                password=base64.b64encode(user_pw.encode()).decode()
            ),
        )

        kopf.adopt(secret)
        core_api.create_namespaced_secret(namespace=namespace, body=secret)

        cnx = mysql.connect(host=cluster_ip, user="root", password=get_k8s_secret(f"{spec['operator']}-mysql-root-password"), database="mysql")
        create_database_user(cnx.cursor(), spec["database"], spec["username"], name)
    except mysql.Error as err:
        LOG.error(f"Exception when connecting to MySQL: {err}")
        raise kopf.TemporaryError(f"Failed to connect to MySQL: {err}", delay=5)
    except ApiException as e:
        LOG.error(f"Exception when calling CoreV1Api->read_namespaced_service: {e}")
        raise kopf.TemporaryError(f"Failed to read service: {e}", delay=5)
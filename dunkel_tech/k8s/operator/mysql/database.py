# This code is licensed under the MIT License.
# See LICENSE.txt for more details.

import kopf
import logging
import kubernetes.client as k8s
import mysql.connector as mysql
from kubernetes.client.rest import ApiException

from dunkel_tech.k8s.operator.mysql.utils import create_database, get_k8s_secret

LOG = logging.getLogger(__name__)

@kopf.on.create('dunkel.tech', 'v1', 'mysqldatabases')
def create_database_resource(spec, name, namespace, logger, **kwargs):
    LOG.info(f"Creating MySQL Database {name} in namespace {namespace}")
    core_api = k8s.CoreV1Api()

    try:
        deploy = core_api.read_namespaced_service(f"{spec['operator']}-mysql", namespace)
        cluster_ip = deploy.spec.cluster_ip
        LOG.debug("Cluster IP: %s", cluster_ip)
        LOG.debug("Creating database %s", name)

        cnx = mysql.connect(host=cluster_ip, user="root", password=get_k8s_secret(f"{spec['operator']}-mysql-root-password"), database="mysql")
        create_database(cnx.cursor(), name)
    except mysql.Error as err:
        LOG.error(f"Exception when connecting to MySQL: {err}")
        raise kopf.TemporaryError(f"Failed to connect to MySQL: {err}", delay=5)
    except ApiException as e:
        LOG.error(f"Exception when calling CoreV1Api->read_namespaced_service: {e}")
        raise kopf.TemporaryError(f"Failed to read service: {e}", delay=5)

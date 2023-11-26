# This code is licensed under the MIT License.
# See LICENSE.txt for more details.

import kopf
import base64
import secrets
import string

import kubernetes.client as k8s
import logging

from kubernetes.client.rest import ApiException

LOG = logging.getLogger(__name__)

def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def get_k8s_secret(secret_name, namespace="default"):
    core_api = k8s.CoreV1Api()

    try:
        secret = core_api.read_namespaced_secret(secret_name, namespace)
        password = base64.b64decode(secret.data["password"]).decode("utf-8")
        return password
    except ApiException as e:
        LOG.error(f"Exception when calling CoreV1Api->read_namespaced_secret: {e}")
        raise kopf.TemporaryError(f"Failed to read secret: {e}", delay=5)


def create_database(cursor, db_name):
    cursor.execute(
        "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))


def create_database_user(cursor, db_name, db_user, db_password):
    cursor.execute(
        "CREATE USER '{}'@'%' IDENTIFIED BY '{}'".format(db_user, db_password))
    cursor.execute(
        "GRANT ALL PRIVILEGES ON {}.* TO '{}'@'%'".format(db_name, db_user))

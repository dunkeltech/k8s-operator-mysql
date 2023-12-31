# Kopf: Example Kubernetes Operator

This is an example kubernetes operator written in python with the help of kopf.

## COPYRIGHT

This code is licensed under the MIT License. See [LICENSE.txt](./LICENSE.txt) file.

## MySQL Operator

This operator is an example operator and definitively NOT production ready.

See [example files](./misc/test.yaml) for usage examples.

## CRDs

### MySQLOperators

This resource creates a mysql pod and a secret with an autogenerated password.

### MySQLDatabases

This resource creates a database in the mysql pod.

### MySQLUsers

This resource creates a user in the mysql pod.


## Debugging with VSCode

If you want to debug with VSCode you can create the following launch.json file:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Run Operator",
            "type": "python",
            "request": "launch",
            "program": "/Users/jan/ENV/k8s-operator/bin/kopf",
            "args": [
                "run",
                "${file}",
            ],
            "justMyCode": true
        }
    ]
}
```
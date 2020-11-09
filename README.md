# Overview 

Simplistic script for generating new certificates for Cockroach. 

```
crdb_ca.py --help
Usage: crdb_ca.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  new-ca    Creates a new Certificate Authority.
  new-node  Generates and signs a new Node key.
  new-user  Generates a signed User Certificate.
```

# Example: 

## 1. First generate a new CA:
```
./crdb_ca.py --help
Usage: crdb_ca.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  new-ca    Creates a new Certificate Authority.
  new-node  Generates and signs a new Node key.
  new-user  Generates a signed User Certificate.

$ ./crdb_ca.py new-ca --help
Usage: crdb_ca.py new-ca [OPTIONS]

  Creates a new Certificate Authority.

Options:
  --ou TEXT       Organizational Unit (default: Cockroach)
  --cn TEXT       Common Name (default: "Cockroach CA")
  --md TEXT       Message Digest (default: sha256
  --days INTEGER  CA Cert lifetime in days (default: 3650)
  --ca-dir PATH   Path to the directory to store the CA files (default: "ca")
  --prefix PATH   Filename prefix (default: "ca")
  --help          Show this message and exit.

(env) [msimmons@mediabox cockroachdb]$ ./crdb_ca.py new-ca --ou "Enterprise IT" --cn "MyCorp"
Created ca
Generating RSA private key, 2048 bit long modulus
........+++
...........+++
e is 65537 (0x10001)
index.txt was reset
serial.txt was reset
$ head ca/ca.crt
-----BEGIN CERTIFICATE-----
MIIC+zCCAeOgAwIBAgIJAPz+fm1KagteMA0GCSqGSIb3DQEBCwUAMCkxFjAUBgNV
BAoMDUVudGVycHJpc2UgSVQxDzANBgNVBAMMBk15Q29ycDAeFw0yMDExMDkxNjQ3
```

## 2. Generate a new node certificate

```
$ ./crdb_ca.py new-node --help
Usage: crdb_ca.py new-node [OPTIONS] [SANS]...

  Generates and signs a new Node key.

  SANS consist of one or more Subject Alternative Names  Example:

  crdb_ca.py new-node --name foo DNS:foo DNS:foo.mydomain IP:1.2.3.4

Options:
  --name TEXT       Node name  [required]
  --cert-path TEXT  Path to store certificates (default: node/)
  --ca-path TEXT    Path to directory that holds CA (default: ca/)
  --ca-prefix TEXT  Prefix for CA key (default: ca)
  --help            Show this message and exit.

$ ./crdb_ca.py new-node --name 'crdb-test' DNS:crdb-test DNS:localhost DNS:127.0.0.1
DNS:crdb-test DNS:localhost DNS:127.0.0.1
Created node
Generating RSA private key, 2048 bit long modulus
................+++
..........+++
e is 65537 (0x10001)
Wrote certificate config to crdb-test.cnf
Generated crdb-test.csr
Using configuration from ca.cnf
Check that the request matches the signature
Signature ok
The Subject's Distinguished Name is as follows
organizationName      :ASN.1 12:'crdb-test'
Certificate is to be certified until Nov  7 16:54:09 2030 GMT (3650 days)

Write out database with 1 new entries
Data Base Updated
```

## 3. Create new user certificate

```
$ ./crdb_ca.py new-user --name 'test-user'
Created user
Generating RSA private key, 2048 bit long modulus
....+++
............................+++
e is 65537 (0x10001)
Using configuration from ca.cnf
Check that the request matches the signature
Signature ok
The Subject's Distinguished Name is as follows
organizationName      :ASN.1 12:'CockroachDB'
commonName            :ASN.1 12:'test-user'
Certificate is to be certified until Nov  7 16:55:13 2030 GMT (3650 days)

Write out database with 1 new entries
Data Base Updated

```



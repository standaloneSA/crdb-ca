#!/usr/bin/env python

import os
import sys
import subprocess
from jinja2 import Template
import click

supported_commands = ['new-ca', 'new-node', 'new-user']

@click.group()
@click.pass_context
def cli(ctx):
    pass

@cli.command('new-ca')
@click.option('--ou', default='Cockroach', help='Organizational Unit')
@click.option('--cn', default='Cockroach CA', help='Common Name')
@click.option('--md', default='sha256', help='Message Digest')
@click.option('--days', default=3650, help='CA Cert lifetime in days')
@click.option('--ca-dir', default='ca', type=click.Path(), help='Path to the directory to store the CA files')
@click.option('--prefix', default='ca', type=click.Path(exists=False))
def new_ca(ou, cn, md, days, ca_dir, prefix):
    t = Template("""
[ ca ]
default_ca = CA_default

[ CA_default ]
default_days = {{ days }}
database = index.txt
serial = serial.txt
default_md = {{ md }}
copy_extensions = copy
unique_subject = no

# Used to create the CA certificate.
[ req ]
prompt=no
distinguished_name = distinguished_name
x509_extensions = extensions

[ distinguished_name ]
organizationName = {{ ou }}
commonName = {{ cn }}

[ extensions ]
keyUsage = critical,digitalSignature,nonRepudiation,keyEncipherment,keyCertSign
basicConstraints = critical,CA:true,pathlen:1

# Common policy for nodes and users.
[ signing_policy ]
organizationName = supplied
commonName = optional

# Used to sign node certificates.
[ signing_node_req ]
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth,clientAuth

# Used to sign client certificates.
[ signing_client_req ]
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = clientAuth
    """)
    try:
        os.mkdir(ca_dir)
        print("Created %s" % ca_dir)
    except FileExistsError:
        print("%s already exists. Continuing" % ca_dir)
    except Exception as err:
        print("Error: Unable to make directory %s: %s" % (ca_dir, str(err)))
        print(err.type)
        sys.exit(1)

    key = "%s/%s.key" % (ca_dir, prefix)
    cnf = "%s/%s.cnf" % (ca_dir, prefix)
    crt = "%s/%s.crt" % (ca_dir, prefix)
    
    # First, make the private key
    if not os.path.exists(key):
        res = subprocess.call(['openssl', 'genrsa', '-out', key, "2048"])
        if res != 0:
            raise Exception("Error calling openssl")
            sys.exit(1)
    else:
        print("%s already exists. Continuing" % key)

    # Next, create the rendered jinja template from above  
    rtext = t.render(ou=ou, cn=cn, days=days, md=md)
    try:
        cnf_file = open(cnf, 'w')
        cnf_file.write(rtext)
        cnf_file.close()
    except Exception as err:
        print(err)
        print("Error writing %s: %s" % (cnf, str(err)))

    res = subprocess.call([
        'openssl', 'req', '-new', '-x509', 
        '-config', cnf, '-key', key, '-out', crt, 
        '-days', str(days), '-batch'])

    if res != 0:
        raise Exception("Error creating certificate request")
        sys.exit(1)
@cli.command('new-node')
@click.option('--name', default='node', help='Node name')
def new_node(name):
    print("In new_node")

@cli.command('new-user')
@click.option('--name', default='user', help='User Name')
def new_user(name):
    print('In new_user')


if __name__ == '__main__':
    cli()

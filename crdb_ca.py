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
@click.option('--ou', default='Cockroach', help='Organizational Unit (default: Cockroach)')
@click.option('--cn', default='Cockroach CA', help='Common Name (default: "Cockroach CA")')
@click.option('--md', default='sha256', help='Message Digest (default: sha256')
@click.option('--days', default=3650, help='CA Cert lifetime in days (default: 3650)')
@click.option('--ca-dir', default='ca', type=click.Path(), help='Path to the directory to store the CA files (default: "ca")')
@click.option('--prefix', default='ca', type=click.Path(exists=False), help='Filename prefix (default: "ca")')
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
        if res:
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

    if res:
        raise Exception("Error creating certificate request")
        sys.exit(1)

    fo = open("%s/index.txt" % ca_dir, "w")
    fo.truncate()
    print("index.txt was reset")
    fo.close()

    fo = open("%s/serial.txt" % ca_dir, "w")
    fo.truncate()
    fo.write("01\n")
    print("serial.txt was reset")
    fo.close()

    

@cli.command('new-node')
@click.option('--name', default=None, required=True, help='Node name')
@click.option('--cert-path', default='node', help='Path to store certificates')
@click.option('--ca-path', default='ca', help='Path to directory that holds CA')
@click.option('--ca-prefix', default='ca', help='Prefix for CA key (default: ca)')
@click.argument('sans', default=None, nargs=-1)
def new_node(name, cert_path, ca_path, ca_prefix, sans):
    """ SANS consist of one or more Subject Alternative Names 

        Example: \n
        crdb_ca.py new-node --name foo DNS:foo DNS:foo.mydomain IP:1.2.3.4
    """
    template = Template("""
# OpenSSL node configuration file
[ req ]
prompt=no
distinguished_name = distinguished_name
req_extensions = extensions

[ distinguished_name ]
organizationName = {{ name }}

[ extensions ]
subjectAltName = {{ SANstring }}
    """)
    SANstring = ' '.join(sans)
    #TODO - check the SAN formatting
    print(SANstring)
    
    # Create the node's certificate directory
    try:
        os.mkdir(cert_path)
        print("Created %s" % cert_path)
    except FileExistsError:
        print("%s already exists. Continuing" % cert_path)
    except Exception as err:
        print("Error: %s" % str(err))
        sys.exit(1)

    key = "%s.key" % name
    crt = "%s.crt" % name
    cnf = "%s.cnf" % name
    csr = "%s.csr" % name

    ca_cnf = "%s.cnf" % ca_prefix
    ca_key = "%s.key" % ca_prefix
    ca_crt = "%s.crt" % ca_prefix
    
    # Generate the node key
    if not os.path.exists(key):
        res = subprocess.call(['openssl', 'genrsa', '-out', key, '2048'], cwd=cert_path)
        if res:
            print("Error generating node private key")
            sys.exit(1)
    else:
        print("Key already exists. Not creating a new one.")
    
    # Generate the node's config 
    cnf_text = template.render(name=name, SANstring=SANstring)
    fo = open("%s/%s" % (cert_path, cnf), "w")
    fo.truncate()
    fo.write(cnf_text)
    fo.close()
    print("Wrote certificate config to %s" % cnf)
    
    # Generate the CSR
    res = subprocess.call([
        'openssl', 'req', '-new',
        '-config', cnf,
        '-key', key,
        '-out', csr,
        '-batch'
        ], cwd=cert_path)
    if res:
        print("Error generating CSR")
        sys.exit(1)
    print("Generated %s" % csr)

    # Sign the CSR with the CA
    res = subprocess.call([ 'openssl', 'ca', 
        '-config', ca_cnf,
        '-keyfile', ca_key,
        '-cert', ca_crt,
        '-policy', 'signing_policy',
        '-extensions', 'signing_node_req',
        '-out', "../%s/%s" % (cert_path, crt),
        '-outdir', "../%s/" % cert_path,
        '-in', "../%s/%s" % (cert_path, csr), 
        '-batch'
        ], cwd=ca_path)
    if res:
        print("Error signing certificate")
        sys.exit(1)

@cli.command('new-user')
@click.option('--name', default='user', help='User Name')
def new_user(name):
    print('In new_user')


if __name__ == '__main__':
    cli()

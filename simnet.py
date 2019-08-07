#!/usr/bin/env python3

import base64
import binascii
import click
import json
import os
import pem
import requests
import shutil
import time

from twisted.internet import ssl

class Node:
    def __init__(self, path, rpc_port, rest_port, port):
        self.path = path
        self.rpc_port = rpc_port
        self.rest_port = rest_port
        self.port = port

    def macaroon(self):
        return f'{self.path}/data/chain/bitcoin/simnet/admin.macaroon'

    def cert(self):
        return f'{self.path}/tls.cert'

    @classmethod
    def from_index(cls, node_index):
        return Node(f'node_{node_index}', 10000 + node_index, 8000 + node_index, 11000 + node_index)

def start_lnd(node):
    lnd = f'''
    lnd \
    --alias={node.path} \
    --lnddir={node.path} \
    --rpclisten=localhost:{node.rpc_port} \
    --listen=localhost:{node.port} \
    --restlisten=localhost:{node.rest_port} \
    --debuglevel=info \
    --bitcoin.simnet \
    --bitcoin.active \
    --bitcoin.node=btcd \
    --btcd.rpcuser=kek \
    --btcd.rpcpass=kek \
    --configfile=lnd.conf \
    > /dev/null &
    '''
    os.system(lnd) 

def lndconnect_node(node):
    chain = pem.parse_file(node.cert())
    chainCert = ssl.Certificate.loadPEM(str(chain[0]))
    cert = base64.b64encode(chainCert.dump())

    with open(node.macaroon(), 'rb') as macaroon_file:
        macaroon = base64.urlsafe_b64encode(macaroon_file.read())

    click.echo(click.style(f'lndconnect://127.0.0.1:{node.rpc_port}?cert={cert.decode()}&macaroon={macaroon.decode()}', fg='green'))

def seed(node):
    url = f'https://localhost:{node.rest_port}/v1/genseed'
    r = requests.get(url, verify=node.cert())
    return r.json()['cipher_seed_mnemonic']

def init_lnd(node):
    url = f'https://localhost:{node.rest_port}/v1/initwallet'
    data = {
        'wallet_password': base64.b64encode(b'12341234').decode(),
        'cipher_seed_mnemonic': seed(node),
    }
    r = requests.post(url, verify=node.cert(), data=json.dumps(data))
    click.echo(f'[{node.path}] wallet created')

def start_node(node):
    click.echo(f'[{node.path}] started')
    start_lnd(node)
    time.sleep(2)
    init_lnd(node)
    
def post(node, url):
    with open(node.macaroon(), 'rb') as macaroon_file:
        macaroon = binascii.hexlify(macaroon_file.read())

    url = f'https://localhost:{node.rest_port}/v1/{url}'
    r = requests.get(
        url, 
        verify=node.cert(),
        headers={
            'Grpc-Metadata-macaroon': macaroon
        }
    )
    return r.json()

def address(node):
    json = post(node, 'newaddress')
    return json['address']

def set_mining_node_index(index):
    dest = address(Node.from_index(index))

    os.system('killall btcd')
    time.sleep(2)
    os.system(f'btcd --simnet --txindex --rpcuser=kek --rpcpass=kek --miningaddr={dest} > /dev/null &')

@click.command()
@click.option('--count', '-c',  default=2)
def start(count):
    """Start and initialize COUNT nodes"""
    click.echo('starting btcd')
    btcd = 'btcd --txindex --simnet --rpcuser=kek --rpcpass=kek > /dev/null &'
    os.system(btcd)
    
    for index in range(0, count):
        start_node(Node.from_index(index))

    time.sleep(2)
    set_mining_node_index(0)
    lndconnect_node(Node.from_index(0))

@click.command()
def stop():
    """Stop btcd, lnd and remove all node data"""
    os.system('killall lnd')
    os.system('killall btcd')
    
    index = 0
    while True:
        node = Node.from_index(index)
        try:
            shutil.rmtree(node.path)
        except:
            click.echo(f'removed {index} nodes.')
            break
        index += 1

@click.command()
@click.argument('cmd')
@click.option('--node', '-n', 'node_index', default=0)
def lncli(cmd, node_index):
    """Run lncli commands for a node"""
    node = Node.from_index(node_index)
    os.system(f'lncli --tlscertpath={node.cert()} --rpcserver=localhost:{node.rpc_port} --macaroonpath={node.macaroon()} {cmd}')

@click.command()
@click.argument('node_index', default=0)
def lndconnect(node_index):
    """Display the lndconnect url for a node"""
    lndconnect_node(Node.from_index(node_index))

@click.command()
@click.argument('node_index', type=int)
def set_mining_node(node_index):
    """Set the node receiving mined blocks"""
    set_mining_node_index(node_index)

@click.command()
@click.argument('count', default=1)
def gen_block(count):
    """Generate COUNT blocks to the current mining-node"""
    os.system(f'btcctl --simnet --rpcuser=kek --rpcpass=kek generate {count} &> /dev/null')

@click.command()
@click.argument('node_index', default=0)
def peer(node_index):
    """Show the address (identity_pubkey@host) of a node."""
    node = Node.from_index(node_index)
    pub_key = post(node, 'getinfo')['identity_pubkey']
    address = f'{pub_key}@localhost:{node.port}'
    click.echo(click.style(address, fg='green'))

@click.group()
def cli():
    """Simplify lnd simnets."""

cli.add_command(start)
cli.add_command(stop)
cli.add_command(lndconnect)
cli.add_command(gen_block)
cli.add_command(lncli)
cli.add_command(peer)
cli.add_command(set_mining_node)

if __name__ == '__main__':
    cli()


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

from pathlib import Path
from twisted.internet import ssl

class Node:
    def __init__(self, name, rpc_port, rest_port, port):
        self.name = name
        self.rpc_port = rpc_port
        self.rest_port = rest_port
        self.port = port

    def macaroon(self):
        return f'{self.path()}/data/chain/bitcoin/simnet/admin.macaroon'

    def cert(self):
        return f'{self.path()}/tls.cert'

    def path(self):
        return f'{Path.home()}/.simnet/{self.name}'

    @classmethod
    def from_index(cls, node_index):
        return Node(f'node_{node_index}', 10000 + node_index, 8000 + node_index, 11000 + node_index)

def start_lnd(node):
    lnd = f'''
    lnd \
    --maxpendingchannels=100 \
    --alias={node.name} \
    --lnddir={node.path()} \
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
    click.echo(f'[{node.name}] started lnd ({node.path()})')

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
    r = requests.post(
        url, 
        verify=node.cert(), 
        data=json.dumps(data)
    )
    click.echo(f'[{node.name}] wallet created')

def post(node, url, data={}):
    with open(node.macaroon(), 'rb') as macaroon_file:
        macaroon = binascii.hexlify(macaroon_file.read())

    url = f'https://localhost:{node.rest_port}/v1/{url}'
    r = requests.post(
        url, 
        verify=node.cert(),
        headers={
            'Grpc-Metadata-macaroon': macaroon
        },
        data=json.dumps(data)
    )
    return r.json()

def get(node, url, data={}):
    with open(node.macaroon(), 'rb') as macaroon_file:
        macaroon = binascii.hexlify(macaroon_file.read())

    url = f'https://localhost:{node.rest_port}/v1/{url}'
    r = requests.get(
        url, 
        verify=node.cert(),
        headers={
            'Grpc-Metadata-macaroon': macaroon
        },
        data=json.dumps(data)
    )
    return r.json()

def address(node):
    json = get(node, 'newaddress')
    return json['address']

def start_btcd(mining_address=None):
    btcd = 'btcd --txindex --simnet --rpcuser=kek --rpcpass=kek'
    if mining_address:
        btcd += f' --miningaddr={mining_address}'
    btcd += ' > /dev/null &'
    os.system(btcd)

def _set_mining_node(index):
    dest = address(Node.from_index(index))

    os.system('killall -9 btcd')
    time.sleep(2)
    start_btcd(dest)

def run_lncli(node, cmd):
    os.system(f'lncli --tlscertpath={node.cert()} --rpcserver=localhost:{node.rpc_port} --macaroonpath={node.macaroon()} {cmd}')

def _block(count):
    os.system(f'btcctl --simnet --rpcuser=kek --rpcpass=kek generate {count} &> /dev/null')
    click.echo(f'mined {count} blocks')

@click.command()
@click.option('--count', '-c',  default=2)
def init(count):
    """Start and initialize COUNT nodes"""
    click.echo('starting btcd')
    start_btcd()
    
    for index in range(0, count):
        node = Node.from_index(index)
        start_lnd(node)
        time.sleep(2)
        init_lnd(node)

    time.sleep(2)
    lndconnect_node(Node.from_index(0))

    time.sleep(5)
    _set_mining_node(1)
    time.sleep(3)

    _block(150)

@click.command()
def clean():
    """Stop btcd, lnd and remove all node data"""
    os.system('killall -9 lnd')
    os.system('killall -9 btcd')
    
    index = 0
    while True:
        node = Node.from_index(index)
        try:
            shutil.rmtree(node.path())
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
    run_lncli(node, cmd)

@click.command()
@click.argument('node_index', default=0)
def lndconnect(node_index):
    """Display the lndconnect url for a node"""
    lndconnect_node(Node.from_index(node_index))

@click.command()
@click.argument('count', default=1)
def block(count):
    """Generate COUNT blocks"""
    _block(count)

@click.command()
@click.argument('node_index', default=0)
def peer(node_index):
    """Show the address (identity_pubkey@host) of a node."""
    node = Node.from_index(node_index)
    pub_key = get(node, 'getinfo')['identity_pubkey']
    address = f'{pub_key}@localhost:{node.port}'
    click.echo(click.style(address, fg='green'))

@click.command()
@click.argument('node_index', type=int)
def start(node_index):
    """Start a specific node"""
    node = Node.from_index(node_index)
    start_lnd(node)
    time.sleep(2)
    data = {
        'wallet_password': base64.b64encode(b'12341234').decode()
    }
    post(node, 'unlockwallet', data)

@click.command()
@click.argument('node_index', type=int)
def stop(node_index):
    """Stop a specific node"""
    node = Node.from_index(node_index)
    run_lncli(node, 'stop')

def _fund(node_index, amount):
    node = Node.from_index(node_index)
    sending_node = Node.from_index(1)
    destination_address = address(node)
    run_lncli(sending_node, f'sendcoins {destination_address} {amount}')

@click.command()
@click.argument('node_index', type=int)
@click.option('--amount', '-a',  default=100000000)
def fund(node_index, amount):
    """Send AMOUNT satoshis from node_1 to NODE_INDEX"""
    node = Node.from_index(node_index)
    sending_node = Node.from_index(1)
    destination_address = address(node)
    run_lncli(sending_node, f'sendcoins {destination_address} {amount}')

@click.group()
def cli():
    """Simplify lnd simnets."""

cli.add_command(init)
cli.add_command(clean)
cli.add_command(lndconnect)
cli.add_command(block)
cli.add_command(lncli)
cli.add_command(peer)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(fund)

if __name__ == '__main__':
    cli()


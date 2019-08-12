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

root = f'{Path.home()}/.simnet/'
btcd_log = f'{root}btcd.log'
btcd_dir = f'{root}btcd'

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
        return f'{root}{self.name}'

    def log(self):
        return f'{root}{self.name}.log'

    @classmethod
    def from_index(cls, node_index):
        return Node(f'node_{node_index}', 10000 + node_index, 8000 + node_index, 11000 + node_index)

# Read from a log file as it's being written using python
# https://stackoverflow.com/questions/3290292/read-from-a-log-file-as-its-being-written-using-python
def follow(thefile):
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

def wait_for_log(path, string):
    with open(path, 'r') as log_file:
        for line in follow(log_file):
            if string in line:
                return

def wait_for_file(file_path):
    while not os.path.exists(file_path):
        time.sleep(0.1)

def start_lnd(node):
    lnd = f'''
    lnd \
    --maxpendingchannels=100 \
    --alias={node.name} \
    --lnddir={node.path()} \
    --rpclisten=localhost:{node.rpc_port} \
    --listen=localhost:{node.port} \
    --restlisten=localhost:{node.rest_port} \
    --debuglevel=debug \
    --bitcoin.simnet \
    --bitcoin.active \
    --bitcoin.node=btcd \
    --btcd.rpcuser=kek \
    --btcd.rpcpass=kek \
    --configfile=lnd.conf \
    &> {node.log()} &
    '''
    os.system(lnd) 

    wait_for_file(node.log())
    wait_for_log(node.log(), 'Waiting for wallet encryption password.')

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
    max_tries = 20
    while True:
        try:
            json = get(node, 'newaddress')
            return json['address']
        except Exception as e:
            if max_tries == 0:
                raise e

            time.sleep(0.3)
            max_tries -= 1

def start_btcd(mining_address=None):
    btcd = f'btcd --txindex --simnet --rpcuser=kek --rpcpass=kek --datadir={btcd_dir}'
    if mining_address:
        btcd += f' --miningaddr={mining_address}'
    btcd += f' &> {btcd_log} &'
    os.system(btcd)

def _set_mining_node(node):
    dest = address(node)

    os.system('killall -9 btcd')
    time.sleep(2)
    start_btcd(dest)

def run_lncli(node, cmd):
    os.system(f'lncli --tlscertpath={node.cert()} --rpcserver=localhost:{node.rpc_port} --macaroonpath={node.macaroon()} {cmd}')

def _block(count):
    os.system(f'btcctl --simnet --rpcuser=kek --rpcpass=kek generate {count} 2> /dev/null | jq .[] | wc -l')
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
        wait_for_file(node.cert())
        init_lnd(node)

    first_node = Node.from_index(0)
    wait_for_file(first_node.macaroon())
    lndconnect_node(first_node)
    
    if count > 1:
        mining_node = Node.from_index(1)
        wait_for_file(mining_node.macaroon())
        _set_mining_node(mining_node)
        time.sleep(4)
        _block(150)

@click.command()
def clean():
    """Stop btcd, lnd and remove all node data"""
    os.system('killall -9 lnd')
    os.system('killall -9 btcd')
    
    shutil.rmtree(btcd_dir)
    os.remove(btcd_log)

    index = 0
    while True:
        node = Node.from_index(index)
        try:
            shutil.rmtree(node.path())
            os.remove(node.log())
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


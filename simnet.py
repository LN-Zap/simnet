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

alice = Node('alice', 10001, 8001, 10011)
bob = Node('bob', 10002, 8002, 10012)

nodes = [alice, bob]

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
    click.echo(f'unlocked lnd at {node.path}')

def start_node(node):
    click.echo(f'starting lnd at {node.path}')
    start_lnd(node)
    time.sleep(2)
    init_lnd(node)
    
def stop_node(node):
    shutil.rmtree(node.path, ignore_errors=True)

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

@click.command()
def start():
    click.echo('starting btcd')
    btcd = 'btcd --txindex --simnet --rpcuser=kek --rpcpass=kek > /dev/null &'
    os.system(btcd)
    
    for node in nodes:
        start_node(node)

    time.sleep(2)
    set_mining_node_index(0)
    lndconnect_node(nodes[0])

@click.command()
def stop():
    os.system('killall lnd')
    os.system('killall btcd')
    
    for node in nodes:
        stop_node(node)

@click.command()
@click.argument('cmd')
@click.option('--node', '-n', default=0)
def lncli(cmd, node):
    selected_node = nodes[node]
    os.system(f'lncli --tlscertpath={selected_node.cert()} --rpcserver=localhost:{selected_node.rpc_port} --macaroonpath={selected_node.macaroon()} {cmd}')

@click.command()
@click.option('--node', '-n', default=0)
def lndconnect(node):
    lndconnect_node(nodes[node])

def set_mining_node_index(index):
    dest = address(nodes[index])

    os.system('killall btcd')
    time.sleep(2)
    os.system(f'btcd --simnet --txindex --rpcuser=kek --rpcpass=kek --miningaddr={dest} > /dev/null &')

@click.command()
@click.argument('node_index', type=int)
def set_mining_node(node_index):
    set_mining_node_index(node_index)

@click.command()
@click.argument('count', default=1)
def gen_block(count):
    os.system(f'btcctl --simnet --rpcuser=kek --rpcpass=kek generate {count} &> /dev/null')

@click.command()
@click.option('--node', '-n', default=0)
def peer(node):
    n = nodes[node]
    pub_key = post(n, 'getinfo')['identity_pubkey']
    address = f'{pub_key}@localhost:{n.port}'
    click.echo(click.style(address, fg='green'))

@click.group()
def cli():
    pass

cli.add_command(start)
cli.add_command(stop)
cli.add_command(lndconnect)
cli.add_command(gen_block)
cli.add_command(lncli)
cli.add_command(peer)
cli.add_command(set_mining_node)

if __name__ == '__main__':
    cli()


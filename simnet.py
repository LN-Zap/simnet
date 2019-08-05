#!/usr/bin/env python3

import base64
import click
import json
import os
import pem
import requests
import shutil
import time

from twisted.internet import ssl

class Node:
    def __init__(self, path, rpc_port, rest_port, port, seed):
        self.path = path
        self.rpc_port = rpc_port
        self.rest_port = rest_port
        self.port = port
        self.seed = seed

alice = Node('alice', 10001, 8001, 10011, ['absent', 'describe', 'disagree', 'device', 'globe', 'pipe', 'monkey', 'bracket', 'bid', 'thumb', 'ice', 'lawn', 'mango', 'stairs', 'pipe', 'abuse', 'jar', 'buffalo', 'mixture', 'arrange', 'clay', 'this', 'cactus', 'slice'])
bob = Node('bob', 10002, 8002, 10012, ['absorb', 'filter', 'arrow', 'seminar', 'rebuild', 'abuse', 'topple', 'tape', 'museum', 'wrestle', 'circle', 'view', 'spell', 'slide','giraffe', 'switch', 'chimney', 'super', 'marble', 'omit', 'leopard', 'parent', 'recycle', 'either'])

@click.group()
def cli():
    pass

def start_lnd(node):
    lnd = f'''
    lnd \
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
    chain = pem.parse_file(f'{node.path}/tls.cert')
    chainCert = ssl.Certificate.loadPEM(str(chain[0]))
    cert = base64.b64encode(chainCert.dump())

    with open(f'{node.path}/data/chain/bitcoin/simnet/admin.macaroon', 'rb') as macaroon_file:
        macaroon = base64.urlsafe_b64encode(macaroon_file.read())

        click.echo(click.style(f'lndconnect://127.0.0.1:{node.rpc_port}?cert={cert.decode()}&macaroon={macaroon.decode()}', fg='green'))

@click.command()
def lndconnect():
    lndconnect_node(alice)

def init_lnd(node):
    cert_path = f'{node.path}/tls.cert'
    url = f'https://localhost:{node.rest_port}/v1/initwallet'
    data = {
        'wallet_password': base64.b64encode(b'12341234').decode(),
        'cipher_seed_mnemonic': node.seed,
    }
    r = requests.post(url, verify=cert_path, data=json.dumps(data))
    click.echo(f'unlocked lnd at {node.path}')

@click.command()
def init():
    init_lnd(alice)

def start_node(node):
    click.echo(f'starting lnd at {node.path}')
    start_lnd(node)
    time.sleep(2)
    init_lnd(node)
    
@click.command()
def start():
    click.echo('starting btcd')
    btcd = 'btcd --txindex --simnet --rpcuser=kek --rpcpass=kek > /dev/null &'
    os.system(btcd)
    
    start_node(alice)
    start_node(bob)

    time.sleep(2)
    lndconnect_node(alice)

def stop_node(node):
    shutil.rmtree(node.path, ignore_errors=True)

@click.command()
def stop():
    os.system('killall lnd')
    os.system('killall btcd')
    
    stop_node(alice)
    stop_node(bob)

cli.add_command(start)
cli.add_command(stop)
cli.add_command(init)
cli.add_command(lndconnect)

if __name__ == '__main__':
    cli()


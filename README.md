# simnet

Watch the [demo](https://twitter.com/ottosuess/status/1158760429193220096).

## Installation

```
pip3 install https://github.com/LN-Zap/simnet/archive/master.zip
```

Or clone and run:
```
sudo -H pip3 install .
```

You also need to install **jq** (`brew install jq` on a mac).

## Help

```
Usage: simnet [OPTIONS] COMMAND [ARGS]...

Simplify lnd simnets.

Options:
--help  Show this message and exit.

Commands:
block       Generate COUNT blocks
clean       Stop btcd, lnd and remove all node data
fund        Send AMOUNT satoshis from node_1 to NODE_INDEX
init        Start and initialize COUNT nodes
lncli       Run lncli commands for a node
lndconnect  Display the lndconnect url for a node
macaroon    Display the node's macaroon in hex
peer        Show the address (identity_pubkey@host) of a node.
start       Start a specific node
stop        Stop a specific node
```

## Setup bash completion

**bash**:
```
_SIMNET_COMPLETE=source simnet > simnet_complete.sh
```

**zsh**:
```
_SIMNET_COMPLETE=source_zsh simnet > simnet_complete.sh
```

And then you put this into your .bashrc or .zshrc:
```
. /path/to/simnet_complete.sh
```

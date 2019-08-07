# simnet

Watch the [demo](https://twitter.com/ottosuess/status/1158760429193220096).

## Installation

```
pip3 install https://github.com/LN-Zap/simnet/archive/master.zip
```

## Help

```
Usage: simnet [OPTIONS] COMMAND [ARGS]...

Options:
--help  Show this message and exit.

Commands:
gen-block
lncli
lndconnect
peer
set-mining-node
start
stop
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

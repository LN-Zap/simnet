REST_PORT_1=8001
LN_ROOT_1="alice"
SEED_1="\"absent\", \"describe\", \"disagree\", \"device\", \"globe\", \"pipe\", \"monkey\", \"bracket\", \"bid\", \"thumb\", \"ice\", \"lawn\", \"mango\", \"stairs\", \"pipe\", \"abuse\", \"jar\", \"buffalo\", \"mixture\", \"arrange\", \"clay\", \"this\", \"cactus\", \"slice\""
RPC_PORT_1=10001
PORT_1=10011

REST_PORT_2=8002
LN_ROOT_2="bob"
SEED_2="\"absorb\", \"filter\", \"arrow\", \"seminar\", \"rebuild\", \"abuse\", \"topple\", \"tape\", \"museum\", \"wrestle\", \"circle\", \"view\", \"spell\", \"slide\",\"giraffe\", \"switch\", \"chimney\", \"super\", \"marble\", \"omit\", \"leopard\", \"parent\", \"recycle\", \"either\""
RPC_PORT_2=10002
PORT_1=10012

lncli1="lncli --rpcserver=localhost:$RPC_PORT_1 --tlscertpath=$LN_ROOT_1/tls.cert --macaroonpath=$LN_ROOT_1/data/chain/bitcoin/simnet/admin.macaroon"
lncli2="lncli --rpcserver=localhost:$RPC_PORT_2 --tlscertpath=$LN_ROOT_2/tls.cert --macaroonpath=$LN_ROOT_2/data/chain/bitcoin/simnet/admin.macaroon"


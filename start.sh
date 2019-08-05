source var.sh

btcd --txindex --simnet --rpcuser=kek --rpcpass=kek > /dev/null &
mkdir alice bob

start_lnd()
{
    lnd --lnddir=$2 --rpclisten=localhost:$4 --listen=localhost:$5 --restlisten=localhost:$1 --debuglevel=info --bitcoin.simnet --bitcoin.active --bitcoin.node=btcd --btcd.rpcuser=kek --btcd.rpcpass=kek --configfile=lnd.conf > /dev/null &
    
    /bin/sleep 2s
    
    curl -s \
        --cacert $2/tls.cert \
        -X POST -d "{\"wallet_password\": \"$(echo "12341234" | tr -d '\n' | base64)\", \"cipher_seed_mnemonic\": [$3] }" \
        https://localhost:$1/v1/initwallet
}


start_lnd $REST_PORT_1 $LN_ROOT_1 "$SEED_1" $RPC_PORT_1 $PORT1
start_lnd $REST_PORT_2 $LN_ROOT_2 "$SEED_2" $RPC_PORT_2 $PORT2

sleep 5s

echo "============ bob ============" 
$lncli1 getinfo | jq

echo "============ alice ============" 
$lncli2 getinfo | jq

echo
lndconnect --port=$RPC_PORT_1 --adminmacaroonpath=$LN_ROOT_1/data/chain/bitcoin/simnet/admin.macaroon --tlscertpath=$LN_ROOT_1/tls.cert -jl


source var.sh

address=$($lncli1 newaddress np2wkh | jq .address)
killall btcd
sleep 2
btcd --simnet --txindex --rpcuser=kek --rpcpass=kek --miningaddr=$address > /dev/null &
sleep 2
btcctl --simnet --rpcuser=kek --rpcpass=kek generate $1 > /dev/null

sleep 1
$lncli1 walletbalance | jq


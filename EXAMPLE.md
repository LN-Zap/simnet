## Example workflow with the simnet tool
Set up a local simnet with 2 nodes, open a channel and pay an invoice.

#### Setup simnet

```console
$ simnet init
starting btcd
[node_0] started lnd (/Users/ottosuess/.simnet/node_0)
[node_0] wallet created
[node_1] started lnd (/Users/ottosuess/.simnet/node_1)
[node_1] wallet created
lndconnect://127.0.0.1:10000?cert=MIICRDCCAeqgAwIBAgIQSATB9j8NPCwLIomeuE8yJDAKBggqhkjOPQQDAjA8MR8wHQYDVQQKExZsbmQgYXV0b2dlbmVyYXRlZCBjZXJ0MRkwFwYDVQQDExAweEU5Mjc0NDgwLmxvY2FsMB4XDTE5MTAwODA4MDgyOVoXDTIwMTIwMjA4MDgyOVowPDEfMB0GA1UEChMWbG5kIGF1dG9nZW5lcmF0ZWQgY2VydDEZMBcGA1UEAxMQMHhFOTI3NDQ4MC5sb2NhbDBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABMWWqG4In0Ulq/XFiTkZ3AoBubvFeVCw+rFZn9iGHmPATMLYz8Oo4RdgnZHumI9ufpHo7+DLhyMOR4cZzo8CD4yjgc0wgcowDgYDVR0PAQH/BAQDAgKkMA8GA1UdEwEB/wQFMAMBAf8wgaYGA1UdEQSBnjCBm4IQMHhFOTI3NDQ4MC5sb2NhbIIJbG9jYWxob3N0ggR1bml4ggp1bml4cGFja2V0hwR/AAABhxAAAAAAAAAAAAAAAAAAAAABhxD+gAAAAAAAAAAAAAAAAAABhxD+gAAAAAAAABDHuAn2fRTAhwTAqAHehxD+gAAAAAAAAHChp//+mU4bhxD+gAAAAAAAABIN4dLdO7KahwQKCwAHMAoGCCqGSM49BAMCA0gAMEUCIQDfzTch/2xHJ/1wkGx3InIzU8dp5MPY/z+NAEttXdkAVQIgeczSpf9r08Uzw8peotPQDMInLByMbPtRMhs6delII8E=&macaroon=AgEDbG5kAs8BAwoQLiMVI_RkpIegRNvUrs6FJBIBMBoWCgdhZGRyZXNzEgRyZWFkEgV3cml0ZRoTCgRpbmZvEgRyZWFkEgV3cml0ZRoXCghpbnZvaWNlcxIEcmVhZBIFd3JpdGUaFgoHbWVzc2FnZRIEcmVhZBIFd3JpdGUaFwoIb2ZmY2hhaW4SBHJlYWQSBXdyaXRlGhYKB29uY2hhaW4SBHJlYWQSBXdyaXRlGhQKBXBlZXJzEgRyZWFkEgV3cml0ZRoSCgZzaWduZXISCGdlbmVyYXRlAAAGIFsakFnDSDscbePHADcjhcBFN53geYTgFPxkJLq07Zqe
     400
mined 400 blocks
```
*Connect your iOS app to the lndconnect url.*

#### Add some sats to node 0 (the node you just connected to)
```console
$ simnet fund 0
{
    "txid": "5a49bfd5ec5317fa78f2ad885634506236c2e6dc6242715101feed3eb0e420cc"
}
$ simnet block
       1
mined 1 blocks
```

#### Display peer address of node 1 to open a channel
```console
$ simnet peer 1
0217496645ab33b7889dfb98901ce2c5a78ec3876d56936f5551b0e10abcdf07b6@localhost:11001
```
*With the iOS app, open a channel to that address.*

#### Mine 6 blocks to confirm the channel
```console
$ simnet block 6
       6
mined 6 blocks
```

#### Create an invoice from node 1
```console
$ simnet lncli "addinvoice 10" --node 1
{
	"r_hash": "b4a8cbe0d5d70116c9624d6df567923a5b0d7c1bf6caab9a659d6789409b0436",
	"pay_req": "lnsb100n1pwem90epp5kj5vhcx46uq3djtzf4kl2euj8fds6lqm7m92hxn9n4ncjsymqsmqdqqcqzpg300alc2n3fu85jpr8luzp7alqwzx3hcq05fqw95f9dtlsdrq8emrulcuv63dj9t7qteaaae2jr5nmhh5ymyt5c8tccq56vam467d29cpwpuy8r",
	"add_index": 1
}
```
*Pay the invoice from the iOS app.*

# Walytis Offchain Storage

P2P encrypted and authenticated communications, based on WalytisIdentities.
## Features

- fully peer-to-peer: no servers of any kind involved
- encrypt and send messages to all peers controlling a specified Walytis Identity
- decrypt and authenticate received messages, validate authorship by a Walytis Identity
- offchain storage: encrypted messages are not stored as Walytis blocks or IPFS content for security
	- a full record of past message metadata is always kept (guaranteed by the Walytis blockchain), message content can be deleted and forgotten if all peers decide to do so.
- identity management features inherited from Walytis Identities:
	- multi-controller support: a Walytis Identity can be managed by any number of controllers
	- identity nesting: Walytis Identities can be controlled by other Walytis Identities
	- ephemeral cryptography: regular key renewal, algorithm-agnostic, room for future algorithms

## Project Status **EXPERIMENTAL**

This library is very early in its development.

The API of this library IS LIKELY TO CHANGE in the near future!

## Documentation

The thorough documentation for this project and the technologies it's based on live in a dedicated repository:

https://github.com/emendir/WalytisTechnologies


## Related Projects
### The Endra Tech Stack

- [IPFS](https://ipfs.tech):  A p2p communication and content addressing protocol developed by ProtocolLabs.
- [Walytis](https://github.com/emendir/Walytis_Beta): A flexible, lightweight, nonlinear database-blockchain, built on IPFS.
- [WalytisIdentities](https://github.com/emendir/WalytisIdentities): P2P multi-controller cryptographic identity management, built on Walytis.
- [WalytisOffchain](https://github.com/emendir/WalytisOffchain): Secure access-controlled database-blockchain, built on WalytisIdentities.
- [WalytisMutability](https://github.com/emendir/WalytisMutability): A Walytis blockchain overlay featuring block mutability.
- [Endra](https://github.com/emendir/Endra): A p2p encrypted messaging protocol with multiple devices per user, built on Walytis.
- [EndraApp](https://github.com/emendir/EndraApp): A p2p encrypted messenger supporting multiple devices per user, built on Walytis.

### Alternative Technologies
- OrbitDB: a distributed IPFS-based database written in go

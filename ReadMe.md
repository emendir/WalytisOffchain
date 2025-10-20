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

## Documentation

The thorough documentation for this project and the technologies it's based on live in a dedicated repository:

- [WalytisOffchain](https://github.com/emendir/WalytisTechnologies/blob/master/WalytisOffchain/1-IntroToWalytisOffchain.md): learn how WalytisOffchain works
- [Walytis Technologies](https://github.com/emendir/WalytisTechnologies): learn about the suite of tools which WalytisOffchain is part of, built to enable developers to easily develop peer-to-peer distributed applications.

## Project Status **EXPERIMENTAL**

This library is very early in its development.

The API of this library IS LIKELY TO CHANGE in the near future!

## [RoadMap](https://github.com/emendir/WalytisTechnologies/blob/master/RoadMap.md)

See the [Walytis Technologies RoadMap](https://github.com/emendir/WalytisTechnologies/blob/master/RoadMap.md) for the current plans for WalytisOffchain in the context of the larger [Walytis Technologies Project](https://github.com/emendir/WalytisTechnologies).

## Contributing

### Get Involved

- GitHub Discussions: if you want to share ideas
- GitHub Issues: if you find bugs, other issues, or would like to submit feature requests
- GitHub Merge Requests: if you think you know what you're doing, you're very welcome!

### Donate

To support me in my work on this and other projects, you can make donations with the following currencies:

- **Bitcoin:** `BC1Q45QEE6YTNGRC5TSZ42ZL3MWV8798ZEF70H2DG0`
- **Ethereum:** `0xA32C3bBC2106C986317f202B3aa8eBc3063323D4`
- [Credit Card, Debit Card, Bank Transfer, Apple Pay, Google Pay, Revolut Pay)](https://checkout.revolut.com/pay/4e4d24de-26cf-4e7d-9e84-ede89ec67f32)

Donations help me:
- dedicate more time to developing and maintaining open-source projects
- cover costs for IT resources

## About the Developer

This project is developed by a human one-man team, publishing under the name _Emendir_.  
I build open technologies trying to improve our world;
learning, working and sharing under the principle:

> _Freely I have received, freely I give._

Feel welcome to join in with code contributions, discussions, ideas and more!

## Open-Source in the Public Domain

I dedicate this project to the public domain.
It is open source and free to use, share, modify, and build upon without restrictions or conditions.

I make no patent or trademark claims over this project.  

Formally, you may use this project under either the: 
- [MIT No Attribution (MIT-0)](https://choosealicense.com/licenses/mit-0/) or
- [Creative Commons Zero (CC0)](https://choosealicense.com/licenses/cc0-1.0/)
licence at your choice. 

## Related Projects

### [Walytis Technologies](https://github.com/emendir/WalytisTechnologies)

An overarching project comprising the development of Walytis and a collection of tools based on it for real-world peer-to-peer communications.

- [Walytis](https://github.com/emendir/Walytis_Beta): A flexible, lightweight, nonlinear database-blockchain, built on IPFS.
- [WalytisIdentities](https://github.com/emendir/WalytisIdentities): P2P multi-controller cryptographic identity management, built on Walytis.
- [WalytisOffchain](https://github.com/emendir/WalytisOffchain): Secure access-controlled database-blockchain, built on WalytisIdentities.
- [WalytisMutability](https://github.com/emendir/WalytisMutability): A Walytis blockchain overlay featuring block mutability.
- [Endra](https://github.com/emendir/Endra): A P2P encrypted messaging protocol with multiple devices per user, built on Walytis.
- [EndraApp](https://github.com/emendir/EndraApp): A P2P encrypted messenger supporting multiple devices per user, built on Walytis.

### [IPFS](https://ipfs.tech)

A P2P communication and content addressing protocol developed by Protocol Labs.
This is the networking foundation which Walytis builds upon.

### Alternative Technologies

- [OrbitDB](https://orbitdb.org/): a distributed IPFS-based database written in go
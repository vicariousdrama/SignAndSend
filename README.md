# SignAndSend

Simple script that reads a json file, signs with the bot in server config, and sends to relays.

This is primarily a test script used to publish arbitrary events to relays that conform to NIP01.

When calling the script, a path to a JSON file should be provided.

The structure of the JSON file may include fields for

- content
- kind (required)
- tags

The created_at for an event will be assigned based on the current time, or by passed in argument.

The pubkey for the event will be taken from the bot's public key derived from private key defined in ./data/serverconfig.json

The event will be signed with the bot's private key defined in ./data/serverconfig.json

Example run

```sh
~/.pyenv/boostzapper/bin/python3 ./signandsend.py ~/path/to/sampleevent.json
```

## Advanced options

If doing a proof of work post, 3 more arguments are allowed after the path of the input file

1. Proof of work bits

Proof of work is checked sequentially from 0 by default and attempts to find a match on leading number of 0 bits of the generated id.  Note that the id is generated based on the content, kind, tags, created_at values and the nonce information is stored in tags. So every sequence increase to work towards the proof of work will alter the resulting id.

Example run for a proof of work 32

```sh
~/.pyenv/boostzapper/bin/python3 ./signandsend.py ~/path/to/sampleevent.json 32
```

2. Nonce starting point

By default nonces increment from 0 to find a solution.  This script can be run as multiple instances, such as separate processes on the same machine, or distributed on multiple machines to find a solution faster.

Example run for a proof of work 32

```sh
~/.pyenv/boostzapper/bin/python3 ./signandsend.py ~/path/to/sampleevent.json 32 100000000000
```

3. Force the created_at date

Separate runs need to use consistent data to find a solution faster. To force the created_at date, supply the timestamp in seconds since epoch as the last argument

```sh
~/.pyenv/boostzapper/bin/python3 ./signandsend.py ~/path/to/sampleevent.json 32 100000000000 1702506180
```

## Installing

To setup, you'll first need to clone the repository

```sh
git clone https://github.com/vicariousdrama/SignAndSend.git
```

## Preparation of Python Environment

To use this script, you'll need to run it with python 3.9 or higher and with the nostr, requests and bech32 packages installed.

First, create a virtual environment (or activate a common one)

```sh
python3 -m venv ~/.pyenv/signandsend
source ~/.pyenv/signandsend/bin/activate
```

Then install the dependencies
```sh
python3 -m pip install nostr@git+https://github.com/vicariousdrama/python-nostr.git
python3 -m pip install requests
python3 -m pip install bech32
python3 -m pip install boto3
```

## Configuring

Make the data folder and initialize config file from the sample

```sh
cd ~/SignAndSend
mkdir -p data
cp -n sample-config.json data/config.json
```

Within this directory, a configuration file named `config.json` is read.  If this file does not exist, one will be created using the `sample-config.json`.

### Nostr Config

Edit the configuration

```sh
nano data/config.json
```

The `nostr` configuration section has these keys

| key | description |
| --- | --- |
| powonly | Indicates whether running in POW only mode. This is the default and will not sign or send messages to relays, but rather output the message nonce and id found after up to 100 billion checks. Set the value to false for signing and sending with the nsec |
| botnsec | The nsec for the primary bot. Can leave blank if only doing POW and not sign and send |
| relays | The list of relays the primary bot uses |

The most critical to define here is the `botnsec`.  This is the id for signing the message once prepared.

The `relays` section contains the list of relays that the bot will use to read events and direct messages, as well as publish profiles (kind 0 metadata), direct message responses (kind 4), replies (kind 1).  Each relay is configured with a url, and permissions for whether it can be read from or written to.



#!~/.pyenv/boostzapper/bin/python3
from nostr.event import Event
from logging.handlers import RotatingFileHandler
import logging
import os
import sys
import time
import botfiles as files
import botnostr as nostr
import botutils as utils

if __name__ == '__main__':

    # Logging to systemd
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
    stdoutLoggingHandler = logging.StreamHandler(stream=sys.stdout)
    stdoutLoggingHandler.setFormatter(formatter)
    logging.Formatter.converter = time.gmtime
    logger.addHandler(stdoutLoggingHandler)
    logFile = f"{files.logFolder}bot.log"
    fileLoggingHandler = RotatingFileHandler(logFile, mode='a', maxBytes=10*1024*1024, 
                                 backupCount=21, encoding=None, delay=0)
    fileLoggingHandler.setFormatter(formatter)
    logger.addHandler(fileLoggingHandler)
    files.logger = logger
    nostr.logger = logger
    # Load server config (using relays, and bot identity)
    serverConfig = files.getConfig(f"{files.dataFolder}config.json")
    nostr.config = serverConfig["nostr"]

    # Load up file
    if len(sys.argv) <= 1:
        logger.error("No file provided")
        quit()
    filetosign = sys.argv[1]
    if not os.path.exists(filetosign):
        logger.error("File does not exist")
        quit()
    jsonobj = files.loadJsonFile(filetosign, None)
    if jsonobj is None:
        logger.error("File was empty or not json")
        quit()
    
    # Proof of Work
    noncetag = -1
    pow = 0
    powcheck = 0
    # Created At
    created_at, _ = utils.getTimes()
    if "created_at" in jsonobj:
        created_at = jsonobj["created_at"]
    if len(sys.argv) > 4:
        created_at = int(sys.argv[4])
    # Prepare event
    if "content" in jsonobj:
        content = jsonobj["content"]
    else:
        content = ""
    if "kind" in jsonobj:
        kind = jsonobj["kind"]
    else:
        logger.error("kind field not found in json")
        quit()
    if "tags" in jsonobj:
        tags = jsonobj["tags"]
        noncetagnum = -1
        noncetagfound = False
        for tag in tags:
            noncetagnum += 1
            if tag[0] == "nonce":
                noncetagfound = True
                pow = int(tag[2])
                powcheck = int(tag[1])
        if noncetagfound: noncetag = noncetagnum
    else:
        tags = None
    if len(sys.argv) > 2:
        pow = int(sys.argv[2])
    if len(sys.argv) > 3:
        powcheck = int(sys.argv[3])
    maxpowcheck = powcheck + 100000000000
    

    if pow > 0:
        if noncetag == -1:
            tags.append(["nonce",str(powcheck),str(pow)])
        else:
            tags[noncetag][1] = str(powcheck)
            tags[noncetag][2] = str(pow)
    if "pubkey" in jsonobj:
        pubkey = jsonobj["pubkey"]
    else:
        pubkey = nostr.getBotPrivateKey().public_key.hex()
    logger.info(f"Preparing message with pubkey {pubkey} and created_at {created_at} for kind {kind}")
    e = Event(created_at=created_at,public_key=pubkey,content=content,kind=kind,tags=tags)
    bigzeros = 0
    if pow > 0:
        thebits = format(int(e.id,16),"064b")
        zeros = 256 - len(thebits)
        if zeros > bigzeros: bigzeros = zeros
        while zeros != pow and powcheck < maxpowcheck:
            powcheck += 1
            tags[noncetag][1] = str(powcheck)
            thebits = format(int(e.id,16),"064b")
            zeros = 256 - len(thebits)
            if zeros > bigzeros: bigzeros = zeros
            if powcheck % 500000 == 0:
                logger.info(f"Working on proof of work {pow} check {powcheck:,} (highest: {bigzeros}) with time {created_at}")
            if zeros >= pow:
                logger.info(e.to_message())
        logger.info(f"Nonce: {powcheck}, POW: {pow}, ID: {e.id}")

    if not "powonly" in jsonobj: quit()
    if jsonobj["powonly"]: quit()

    nostr.getBotPrivateKey().sign_event(e)
    # Connect to relays
    nostr.connectToRelays()
    # Send the event
    nostr.botRelayManager.publish_event(e)
    time.sleep(1)
    # Disconnect from relays
    nostr.disconnectRelays()

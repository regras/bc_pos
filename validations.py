import consensus
import sqldb
import math
import hashlib
import parameter
import time
import datetime

def validateChallenge(block, userStake):
    print("userStake: ", userStake)
    print("block.subuser: ", block.subuser)
    if(int(userStake) >= block.subuser):
        p = float(parameter.tal) / parameter.W
        P_i = 1 - ((1 - p) ** int(userStake))
        D = (-1) * float(math.log(P_i,2))
        target = 2**(256-D)

         #block hash
        b_header = str(block.prev_hash) + str(block.mroot)
        block_hash = hashlib.sha256(b_header).hexdigest()

        #proof hash
        p_header = str(block.node) + str(block.round) + str(block_hash) + str(userStake) #candidate header
        hash_result = hashlib.sha256(p_header).hexdigest()
        print("hash_result: ", hash_result)
        print("block.proof_hash: ", block.proof_hash)
        print("target: ", target)
        if int(hash_result,16) < target and hash_result == block.proof_hash:
            print("HASH VALID")
            return True
    return False

def validateRound(block, bc):
    chainBlock = bc.getLastBlock()
    if block.index > chainBlock.index and block.round > chainBlock.round:
        return True
    return False

def validateBlockHeader(block):
    # check block header
    if block.hash == block.calcBlockhash():
        return True
    return False

def validateBlock(block, lastBlock):
    # check block chaining
    if block.prev_hash == lastBlock.hash:
        return True
    return False


def blockPosition(block, bc, stake):
    #check if the block has a valid threshold
    chainPos, bcPos = validatePositionBlock(block, bc, stake)
    if(chainPos):
        return True, bcPos
    else:
        return False, bc

def validatePositionBlock(block, bc, stake):
    i = 0
    while i < parameter.THRESHOLD:
        if(len(bc.chain)> 1):
            bc.chain.pop()
        chainBlock = bc.getLastBlock()
        if(block.prev_hash == chainBlock.prev_hash and 
           chainBlock.round > block.round and 
           validateChallenge(block, stake)):
            return True, bc
        i = i + 1
    return False, bc

def validateChain(bc, chain, stake):
    lastBlock = bc.getLastBlock()
    for b in chain:
        b=sqldb.dbtoBlock(b)
        if not validateBlockHeader(b): # invalid
            #print("HEADER NOT OK")
            return b, True
        #print("lastblock index",lastBlock.index)
        #print("current block index", b.index) 
        if validateBlock(b, lastBlock):
            #print("BLOCK OK")
            if validateChallenge(b, stake) and validateRound(b,bc) and validateExpectedRound(b,lastBlock):
                print("BLOCO VALIDO SINCRONIZADO")
                lastBlock=b
                bc.addBlocktoBlockchain(b)
                sqldb.writeBlock(b)
                sqldb.writeChain(b)
        else: # fork
            return b, False
    return None, False

def validateExpectedRound(block, lastBlock):
    calculated_rounds = int(math.floor((int(block.arrive_time) - int(lastBlock.arrive_time))/parameter.timeout)) + 1
    expected_round = lastBlock.round + calculated_rounds
    if block.round >= expected_round - 1 and block.round <= expected_round + 1:
        #print("EXPECTED_ROUND", expected_round)
        return True
    else:
        return False

def validateProofHash(block,user_stake,cons):
    blockHash = cons.POS(lastBlock_hash=block.prev_hash, tx=block.merkle)
    

def validateExpectedLocalRound(block):
    nowTime = time.mktime(datetime.datetime.now().timetuple())
    expected_round = int(math.floor((float(block.arrive_time) - float(parameter.GEN_ARRIVE_TIME))/parameter.timeout))
    #if(calculated_rounds == 0 and ((int(block.arrive_time) - int(leaf_arrive_time)) < parameter.timeout)):
    #    calculated_rounds = 1

    #elif((int(block.arrive_time) - int(leaf_arrive_time)) > (calculated_rounds * parameter.timeout)):
    #    calculated_rounds = calculated_rounds + 1    

    #expected_round = leaf_round + calculated_rounds
    if(block.round >= expected_round):
        print("ARRIVE_TIME", block.arrive_time)
        print("CALC TIME", nowTime)
        print("ROUND DIF", int(math.floor((float(nowTime) - float(block.arrive_time))/parameter.timeout)))
        print("BLOCK ROUND", block.round)
        print("EXPECTED_ROUND", expected_round)
    #print("Expected Round")
    #print(leaf_round)
    #print("Block Round")
    #print(block.round)
    if block.round >= expected_round - parameter.roundTolerancy and block.round <= expected_round + parameter.roundTolerancy:
        #print("EXPECTED_ROUND", expected_round)
        return True
    else:
        return False

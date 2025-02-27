from time import sleep

import _testing_utils
import test_private_blockchain
import test_block_sharing
import test_generic_blockchain_features

_testing_utils.PYTEST = False

test_private_blockchain.run_tests()
test_block_sharing.run_tests()
test_generic_blockchain_features.run_tests()
sleep(1)

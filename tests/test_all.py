from time import sleep

import _testing_utils
import test_block_sharing

_testing_utils.PYTEST = False

test_block_sharing.run_tests()
sleep(1)

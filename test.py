from identity.identity import IdentityAccess
from management import identity_management
from identity.did_objects import Key
import tempfile

CRYPTO_FAMILY = "EC-secp256k1"

tempdir1 = tempfile.mkdtemp()
tempdir2 = tempfile.mkdtemp()

key = Key.create(CRYPTO_FAMILY)
ia_1 = IdentityAccess.create(tempdir1, key)
invitation = ia_1.invite_member()
ia_2 = IdentityAccess.join(invitation, tempdir2, key)

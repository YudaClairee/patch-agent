import logging

logger = logging.getLogger(__name__)

def decrypt_token(cred) -> str:
    """
    STUB: GitHub credential decryption is owned by Stream 1 and is not integrated yet.
    Temporary integration boundary - do not use for real GitHub calls.
    """
    logger.warning("[CREDENTIALS STUB] decrypt_token called, but credential integration is pending.")
    raise NotImplementedError("GitHub credential decryption is owned by Stream 1 and is not integrated yet")

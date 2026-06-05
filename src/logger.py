import logging


def construire_logger():
    logging.basicConfig(
        # filename="log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Pour activer le log, supprimer cette ligne.
    logging.disable(logging.CRITICAL)

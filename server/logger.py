import logging


def setup_logger(name="MedicalAssistant"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # decide formatting of the logger
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)

    # prevent duplicate handlers if setup_logger is called multiple times
    if not logger.hasHandlers():
        logger.addHandler(ch)

    return logger


logger = setup_logger()
logger.info("RAG Logger initialized successfully.")

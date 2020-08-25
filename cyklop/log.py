import logging

logger = logging.getLogger('cyklop')


def setup(debug=False, quiet=False):
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING

    logging.basicConfig(level=level,
                        format='%(asctime)s - %(levelname)s: %(message)s')

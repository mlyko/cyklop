import asyncio
import argparse
import resource

from .log import logger, setup as setup_logger
from .runner import ScenarioRunner

NAME = 'cyklop'

DEFAULT_RLIMIT_NOFILE = (65536, 65536)


def _setup_ulimits():
    limits = resource.getrlimit(resource.RLIMIT_NOFILE)
    if limits[0] < DEFAULT_RLIMIT_NOFILE[0]:
        resource.setrlimit(resource.RLIMIT_NOFILE, DEFAULT_RLIMIT_NOFILE)


def _setup_uvloop():
    try:
        import uvloop
    except ImportError:
        logger.warning('Could not use uvloop - not installed')
    else:
        uvloop.install()


def _parse_args():
    parser = argparse.ArgumentParser(prog=NAME,
                                     description='A tool for load testing')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', '--debug', action='store_true',
                       help='turn on debug output')
    group.add_argument('-q', '--quiet', action='store_true',
                       help='turn on quiet output')

    parser.add_argument('-f', '--file', required=True,
                        help='a file implementing a scenario ot run')
    parser.add_argument('-u', '--no-uvloop', action='store_true',
                        help='do not try to use uvloop for better performance')

    return parser.parse_args()


def main():
    args = _parse_args()

    setup_logger(debug=args.debug,
                 quiet=args.quiet)

    # For better performance
    _setup_ulimits()
    if not args.no_uvloop:
        _setup_uvloop()

    logger.info('%s start scenario: %s',
                NAME.capitalize(), args.file)
    # Create an event loop first
    loop = asyncio.get_event_loop()
    runner = ScenarioRunner(args.file)
    try:
        loop.run_until_complete(runner.run())
    except KeyboardInterrupt:
        logger.warning('%s interrupted!', NAME.capitalize())
    else:
        logger.info('%s finished', NAME.capitalize())

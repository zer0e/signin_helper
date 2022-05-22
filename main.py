import argparse
import sys
import os

from genshincheckinhelper.main import run_once

env = os.environ


def runner_parser(ap=None):
    if not ap:
        ap = argparse.ArgumentParser()
    ap.add_argument("--bbs_cookie", nargs="?")
    return ap


def setup_by_args(args):
    if args.bbs_cookie:
        env['COOKIE_BH3'] = env['COOKIE_MIHOYOBBS'] = args.bbs_cookie


def main(argv=None):
    ap = argparse.ArgumentParser()
    runner_parser(ap)
    args = ap.parse_args(argv)
    setup_by_args(args)
    run_once()


if __name__ == "__main__":
    main()

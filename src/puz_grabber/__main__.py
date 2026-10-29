#!/usr/bin/env python3
import argparse
from .config import SOURCES 
from .downloaders import *
from .downloaders import HANDLERS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('puzzle_code', choices=SOURCES.keys())
    
    args = parser.parse_args()
    
    handler = HANDLERS[SOURCES[args.puzzle_code]["source"]]
    handler(args.puzzle_code)

if __name__ == '__main__':
    main()

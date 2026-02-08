#!/usr/bin/env python3
'''
Full demo tests - verify all sections can be imported and called without crashing.
'''

import pytest
import sys

# Mimic demo.py path setup - add both src and root for demo imports
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

from demo import (
    demo_solana,
    demo_usdc,
    demo_escrow,
    demo_reviews,
    demo_mandate,
    demo_discovery,
    demo_reputation,
    demo_reputation_chain,
    main
)

def test_demo_solana():
    '''Test solana section exists and runs.'''
    demo_solana()

def test_demo_usdc():
    '''Test usdc section exists and runs.'''
    demo_usdc()

def test_demo_escrow():
    '''Test escrow section exists and runs.'''
    demo_escrow()

def test_demo_reviews():
    '''Test reviews section exists and runs.'''
    demo_reviews()

def test_demo_mandate():
    '''Test mandate section exists and runs.'''
    demo_mandate()

def test_demo_discovery():
    '''Test discovery section exists and runs.'''
    demo_discovery()

def test_demo_reputation():
    '''Test reputation section exists and runs.'''
    demo_reputation()

def test_demo_reputation_chain():
    '''Test reputation chain section exists and runs.'''
    demo_reputation_chain()

def test_main():
    '''Test full main demo runs end-to-end without crashing.'''
    main()
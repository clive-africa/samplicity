# -*- coding: utf-8 -*-
"""
Created on Thu May  4 15:03:54 2023

@author: chogarth
"""
# To ensure consistency for the user, we elevate these a level
from .scr import scr
from .data import data
from .market import market
from .reinsurance import reinsurance

# We expose these function to allow them to be used easily through the command line
from .main import run_excel, run_ms_access

# Allow for logging in the package
import logging
logger = logging.getLogger('samplexity')

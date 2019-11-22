import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from source import utils

def run():
	print(utils.list_databases('DBSVR03'))

if __name__=='__main__':
	run()
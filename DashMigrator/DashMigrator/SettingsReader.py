#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
from typing import Dict
import configparser
import argparse

def cli_run() -> str:
	"""Reads command line args, if program is run from main
	Only argument 'run' determining 'Test' or 'Prod'
	So, returns string of one of those values

	Args:
		None
	Returns:
		String - Capitalized first four digits of input
			Should be 'Test' or 'Prod'
	"""
	parser = argparse.ArgumentParser(description='Reads in necessary info')
	parser.add_argument('-r', '--run', default='test', help='Which run to perform: test or prod')
	args = parser.parse_args()

	return args.run[:4].capitalize()


def read_config(configPath: str='./config.ini') -> configparser.ConfigParser:
	"""Reads in config file
	Reads config file with conrfigparser module
	Checks config for errors 
	
	Args:
		configPath: String that leads to the config file
	Returns:
		Dict-like parsed config
	"""
	if not os.path.isfile(configPath):
		print ('Config not found. Exiting.')
		sys.exit()

	config = configparser.ConfigParser()
	config.read(configPath)

	config = _clean_path(config, configPath)
	_check_config(config)

	return config


def _clean_path(config: configparser.ConfigParser, 
				configPath: str) -> configparser.ConfigParser:
	"""Renames folder and updates path to remove comma

	Args:
		config: dict-like parsed config
	Returns:
		config, with comma removed from path field
	"""
	newPath = config['Path']['path'].replace(',', '')

	os.rename(config['Path']['path'], newPath)
	config['Path']['path'] = newPath

	with open(configPath, 'w') as f:
		config.write(f)
	
	return config



def _check_config(config: configparser.ConfigParser) -> None:
	"""Makes sure config has all needed sections
	Exits program if missing any needed parts
	Prints out any extra(read ignored) parts, but continues

	Args:
		config: dict-like parsed config
	Returns:
		None
	"""
	parts = ['Database', 'Server', 'Path']
	missing = [
		part 
		for part in parts
		if part not in config.sections()
	]

	extra = [
		section
		for section in config.sections()
		if section not in parts
	]

	if missing:
		out_str = ', '.join(missing)
		print(f'Config missing sections: {out_str} \nExiting')
		sys.exit()

	if extra:
		out_str = ', '.join(extra)
		print(f'Config has extra sections: {out_str}')


def runtime_settings(run: str, configPath: str='./config.ini') -> Dict[str, str]:
	"""Returns dict with runtime settings from config
	Main program to run. Gets config from file, takes out 
	needed information, depening on run type

	Args:
		run: String determining 'Test' or 'Prod'
		configPath: String that leads to the config file
	Returns:
		info: dict with config options
	"""
	config = read_config(configPath)

	paths = {
		k: v 
		for k, v in config['Path'].items()
	}
	info = {
		'db': config['Database'][run],
		'svr': config['Server'][run],
	}

	info.update(paths)

	return info


def main() -> None:
	"""Function that runs if program is run
	* Really just for testing *
	Takes in command line arg of run
	Uses ./config.ini
	Prints out config as dict

	Args:
		None
	Returns:
		None
	"""
	run = cli_run()
	settings = runtime_settings(run)
	print(settings)


if __name__=='__main__':
	main()
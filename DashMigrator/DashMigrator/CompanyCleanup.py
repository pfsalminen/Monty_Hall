#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import pandas as pd


def clean_company(fPath: str) -> bool:
    """Removes CompanyNote field from DASH company table

	Args:
		fPath: String path to dash company table
	Returns:
		bool: Success or failure
	"""
    if not os.path.exists(fPath):
        print('File does not exist')
        return False

    df = pd.read_csv(fPath, encoding='utf-8')
    if 'CompanyNote' in df.columns:
        df.drop(['CompanyNote'], axis=1, inplace=True)

    df.drop_duplicates(inplace=True)
    df.to_csv(fPath, index=False)

    return True

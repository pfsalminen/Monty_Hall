
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
""" storage Defines dataclasses used to store provisioning data
Author: Paul Salminen 2019
"""

from dataclasses import dataclass

@dataclass
class Master:
    """ Master holds broad information for provisioning data
    All variables have set defaults for RM databases
    However, they can be changed to provision anything else
    """

    master_copy: str = 'RMMASTERDB'
    bakLoc: str = ('//DBSVR03/SQLBackups/RMMASTERDB.bak')
    nssLoc: str = '//syncsvr01/c$/Program Files/Netsyncserver/'
    bfLoc: str = '//bfsvr03/BUILDERFILES/RMBFSVR/'
    intLoc: str = '//appsvr08/inetpub/Sites/www.intuitivemobile.com/'
    manager: str = 'MOBILEMANAGER_WEB'

    def sql_bakloc(self):
        """ Transforms bakLoc for MS SQL"""
        return self.bakLoc.replace('/', '\\')


@dataclass
class Company(Master):
    """ Company holds information to provision a database
    Gets broad information from Master
    Some defaults set, for PuroClean/ServPro
    """

    db: str = ''
    svr: str = 'DBSVR03'
    accnt_id: str = ''
    xactnet_addr: str = ''
    tpaID: str = ''
    QBO: bool = False

    def dsn(self):
        """ creates dsn from the server name"""
        return f'SYNC_{self.svr}'

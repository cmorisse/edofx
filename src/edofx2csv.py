#!/usr/local/bin/python
# coding: utf8
#
# Copyright (C) 2010 Cyril MORISSE <cmorisse@boxes3.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
__version__ = "edofx2csv.py v0.1 - mai 2010" 


import sys

import os
import ConfigParser

from edofx import OFXParser
from optparse import OptionParser, OptionGroup

class StatementTransaction(object):
    '''
    Used to store a statement transaction
    '''
    def __init__( self, fitid='', trntype='', dtposted='', trnamt='', name='', memo='' ):
        self.fitid      = fitid
        self.type       = trntype
        self.date       = dtposted
        self.amount     = trnamt
        self.name       = name
        self.memo       = memo 

class Statement(object):
    '''
    Stores one statement
    '''
    def __init__(self, type=''):
        self.type = type
        self.currency = ''
        self.bank_id = ''
        self.branch_id = ''
        self.account_id = ''
        self.start_date = ''
        self.end_date = ''
        self.transaction_list = []
        self.balance = 0
        self.balance_date = ''

    def export_as_csv(self, separator=';', header_line = True):
        tmp = ""
        if header_line:
            tmp += 'ACCOUNT_TYPE%s' % ( separator )
            tmp += 'BANK_ID%s' % ( separator )
            tmp += 'BRANCH_ID%s' % ( separator )
            tmp += 'ACCOUNT_ID%s' % ( separator )
            tmp += 'FITID%s' % ( separator )
            tmp += 'TRANSACTION_TYPE%s' % (separator)
            tmp += 'TRANSACTION_DATE%s' % (separator)
            tmp += 'TRANSACTION_AMOUNT%s' % ( separator )
            tmp += 'TRANSACTION_CREDIT%s' % ( separator )
            tmp += 'TRANSACTION_DEBIT%s' % ( separator )
            tmp += 'TRANSACTION_NAME%s' % ( separator )
            tmp += 'TRANSACTION_MEMO' 
            tmp += '\n'
        
        for e in self.transaction_list:
            tmp += '"%s"%s' % (self.type, separator)
            tmp += '"%s"%s' % (self.bank_id, separator)
            tmp += '"%s"%s' % (self.branch_id, separator)
            tmp += '"%s"%s' % (self.account_id, separator)
            tmp += '"%s"%s' % (e.fitid, separator)
            tmp += '"%s"%s' % (e.type, separator)
            tmp += '"%s"%s' % (e.date.strftime("%d/%m/%Y"), separator)
            tmp += str(e.amount).replace('.',',') + separator
            tmp += ( str(e.amount) if e.amount > 0 else '' ) + separator
            tmp += ( str(e.amount) if e.amount < 0 else '' ) + separator
            tmp += '"%s"%s' % (e.name, separator)
            tmp += '"%s"' % (e.memo)
            tmp += '\n'
        return tmp

# Global OFX file structure is (without self closing tags) :
# OFX
#    SIGNONMSGSRSV1
#    BANKMSGSRSV1
#        STMTTRNRS : On per bank account 
#            TRNUID    : = Account number for Credit Agricole SRA French Bank
#            STATUS
#            STMTRS
#                CURDEF
#                BANKACCTFROM    : account description 
#                BANKTRANLIST
#                    DTSTART
#                    DTEND
#                    STMTRN*     : One per statement
#                LEDGERBAL
#                AVAILBAL
#    CREDITCARDMSGSRSV1
#        CCSTMTTRNRS : On by card 
#            TRNUID    : = Account number for CA
#            STATUS
#            CCSTMTRS
#                CURDEF
#                CCACCTFROM      : credit card description  
#                BANKTRANLIST
#                    DTSTART
#                    DTEND
#                    STMTRN*     : One per statement
#                LEDGERBAL
#                AVAILBAL
#                    
#    

def build_Statement_tree(OFX):
    '''
    visit OFXNode tree to build a Dedicated Object Tree
    '''
    statement_list = []

    if OFX.BANKMSGSRSV1 :
        # For each account statement...
        for aSTMTTRNRS in OFX.BANKMSGSRSV1.STMTTRNRS:
            stmt = Statement('CHECKING')
            stmt.currency   = aSTMTTRNRS.STMTRS.CURDEF.val
            stmt.bank_id    = aSTMTTRNRS.STMTRS.BANKACCTFROM.BANKID.val
            stmt.branch_id  = aSTMTTRNRS.STMTRS.BANKACCTFROM.BRANCHID.val
            stmt.account_id = aSTMTTRNRS.STMTRS.BANKACCTFROM.ACCTID.val
            stmt.start_date = aSTMTTRNRS.STMTRS.BANKTRANLIST.DTSTART.val
            stmt.end_date   = aSTMTTRNRS.STMTRS.BANKTRANLIST.DTEND.val
            # for each transaction in statement
            for s in aSTMTTRNRS.STMTRS.BANKTRANLIST.STMTTRN:
                st          = StatementTransaction()
                st.fitid    = s.FITID.val
                st.type     = s.TRNTYPE.val
                st.date     = s.DTPOSTED.val
                st.amount   = s.TRNAMT.val
                st.name     = s.NAME.val
                st.memo     = s.MEMO.val
                stmt.transaction_list.append(st)
    
            stmt.balance      = aSTMTTRNRS.STMTRS.LEDGERBAL.BALAMT.val
            stmt.balance_date = aSTMTTRNRS.STMTRS.LEDGERBAL.DTASOF.val

            statement_list.append(stmt)

    if OFX.CREDITCARDMSGSRSV1:
        # For each credit card statement...
        for aCCSTMTTRNRS in OFX.CREDITCARDMSGSRSV1.CCSTMTTRNRS:
            stmt = Statement('CREDIT_CARD')
            stmt.currency   = aCCSTMTTRNRS.CCSTMTRS.CURDEF.val
            stmt.bank_id    = ''
            stmt.branch_id  = ''
            stmt.account_id = aCCSTMTTRNRS.CCSTMTRS.CCACCTFROM.ACCTID.val
            
            stmt.start_date = aCCSTMTTRNRS.CCSTMTRS.BANKTRANLIST.DTSTART.val
            stmt.end_date   = aCCSTMTTRNRS.CCSTMTRS.BANKTRANLIST.DTEND.val

            for s in aCCSTMTTRNRS.CCSTMTRS.BANKTRANLIST.STMTTRN:
                st          = StatementTransaction()
                st.fitid    = s.FITID.val
                st.type     = s.TRNTYPE.val
                st.date     = s.DTPOSTED.val
                st.amount   = s.TRNAMT.val
                st.name     = s.NAME.val
                st.memo     = s.MEMO.val
                stmt.transaction_list.append(st)

            stmt.balance      = aCCSTMTTRNRS.CCSTMTRS.LEDGERBAL.BALAMT.val
            stmt.balance_date = aCCSTMTTRNRS.CCSTMTRS.LEDGERBAL.DTASOF.val
    
            statement_list.append(stmt)

    return statement_list


def main(source_file):
    """
        Takes a multi-account OFX file as input and
        output one OFX file per account.
    """
    f = open(source_file)
    p = OFXParser(f.read())
    o = p.parse()
    
    statement_list = build_Statement_tree(o) 
    
    for stmt in statement_list:
        file_name =  'releve_compte_'+stmt.account_id.strip()+'_du_'+str(stmt.start_date.strftime("%d-%m-%Y"))+'_au_'+str(stmt.end_date.strftime("%d-%m-%Y"))+'.csv'
        f = open(file_name,'w')
        f.write(stmt.export_as_csv())
        f.close()
        

if __name__ == '__main__':
    
    usage = "usage: %prog ofx_file"
    parser = OptionParser(usage, version=__version__)
    
    (options, args) = parser.parse_args()
    
    if not args or len(args) > 1 :
        print "18ducks - OFX to CSV converter"
        print
        print "    use ./edofx2csv.py -h or --help for usage instructions."
        print
        sys.exit(0)

    ret = main( args[0] )
    sys.exit(ret)
    

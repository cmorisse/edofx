# coding: utf8
'''
Created on 16 mars 2010

@author: Cyril MORISSE <cmorisse@boxes3.net>

edofx_integration is an example use of edofx parser to parse an OFX
file into a graph of specific classes (Statement and StatementTransaction).

'''
from datetime import date


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
            tmp += '"%s"%s' % (str(e.date), separator)
            tmp += str(e.amount) + separator
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

def render_as_DOT(OFX):
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

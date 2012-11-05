# coding: utf-8
'''
Created on 28 fév. 2009

@author: cyrilm

Obfuscation tests rely on real personal data that I won't supply as fixtures.

So you must add 2 real files in test/fixtures:
- real_file.ofx ; an OFX with at least a BANKMSGSRSV1.  and CREDITCARDMSGSRSV1  
- multi_account_file.ofx ; an OFX file with :
    # both BANKMSGSRSV1 and CREDITCARDMSGSRSV1 nodes 
    # multiple accounts ( several OFX.BANKMSGSRSV1.STMTTRNRS nodes )

If you don't have such files. You can use obfuscated default versions I added in 
test/fixtures/obfuscated_sources and in test/fixtures/obfuscated_sources

'''
import unittest
import logging
import sys
import os
from edofx import OFXParser, OFXNode, OFXObfuscator

class TestLoggingHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.messages_list = list()
        self.last_message=''
        
    def emit(self, record):
        self.last_message = record.msg
        self.messages_list.append(record.msg)

class AcceptanceTests(unittest.TestCase):

    def setUp(self):
        self.logging_handler = TestLoggingHandler()
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("Test OFXObfuscator").addHandler(self.logging_handler)
        self.path = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))+'/fixtures/'
    
    def tearDown(self):
        pass

    def test_01_obfuscate_real_file(self):
        obfuscator = OFXObfuscator(open(self.path+'real_file_no_headers.ofx').read())
        ofx = obfuscator.obfuscate()        

    def test_02_obfuscate_real_file_and_save_as_ofx(self):
        obfuscator = OFXObfuscator(open(self.path+'real_file_no_headers.ofx').read())
        ofx = obfuscator.obfuscate()        

        f = open('output/real_file_obfuscated.ofx','w')
        f.write(ofx)
        f.close()

    def test_03_parse_obfuscated_file_and_save_as_ofx(self):
        '''
        Use filemerge to compare : output/real_file_obfuscated.ofx
        and output/real_file_obfuscated_2.ofx
        '''
        parser = OFXParser(open('output/real_file_obfuscated.ofx').read())
        OFX = parser.parse()

        f = open('output/real_file_obfuscated_2.ofx','w')
        f.write(OFX.ofx_repr())
        f.close()

    def test_04_parse_real_file_and_save_as_obfuscated_ofx(self):
        '''
        This test use OFXNode.obfuscated_ofx_repr() which generates a usable OFX
        '''
        src = open(self.path+'multi_account_file.ofx')
        parser = OFXParser(src.read())
        src.close()

        OFX =parser.parse()
        f = open('output/multi_account_obfuscated.ofx','w')
        f.write(OFX.obfuscated_ofx_repr())
        f.close()

    def test_05_parse_obfuscatedreal_and_save_as_xml(self):
        '''
        This test use OFXNode.obfuscated_ofx_repr() which generates a usable OFX
        '''
        src = open('output/multi_account_obfuscated.ofx')
        parser = OFXParser(src.read())
        src.close()

        OFX =parser.parse()
        f = open('output/multi_account_obfuscated.xml','w')
        f.write(OFX.xml_repr())
        f.close()


if __name__=="__main__":
    unittest.main()
    
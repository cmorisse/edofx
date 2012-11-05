# coding: utf-8
'''
Created on 28 fév. 2009

@author: cyrilm
'''
import unittest
import logging
import sys
import os

from edofx import OFXParser, OFXNode
from edofx_integration import render_as_DOT


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
        logging.getLogger("OFXParser").addHandler(self.logging_handler)
        self.path = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))+'/fixtures/'
    
    def tearDown(self):
        pass
        
  
    def test_01_empty_ofx_file(self):
        parser = OFXParser(open(self.path+'empty.ofx').read())
        self.assertTrue(self.logging_handler.last_message.__contains__("Supplied source string is null"))

    def test_02_opening_tag_file(self):
        '''
        Parse a basic set of tokens
        '''
        parser = OFXParser(open(self.path+'opening_tag.ofx').read())
        tag = parser._OFXParser__read_tag()
        self.assertTrue(tag.type==tag.TYPE_OPENING)
        self.assertTrue(tag.name=='STATUS')

    def test_03_closing_tag_file(self):
        '''
        Parse a basic set of tokens
        '''
        parser = OFXParser(open(self.path+'closing_tag.ofx').read())
        tag = parser._OFXParser__read_tag()
        self.assertTrue(tag.type==tag.TYPE_CLOSING)
        self.assertTrue(tag.name=='STATUS')

    def test_04_selfclosing_tag_file(self):
        '''
        Parse a basic set of tokens
        '''
        parser = OFXParser(open(self.path+'selfclosing_tag.ofx').read())
        tag = parser._OFXParser__read_tag()
        self.assertTrue(tag.type==tag.TYPE_SELFCLOSING)
        self.assertTrue(tag.name=='CODE')
        self.assertTrue(tag.value=='this is a value with 1 number and 2 special chars :(')
 
    def test_05_real_ofx_content(self):
        """
        Parse a basic set of tokens
        """
        parser = OFXParser(open(self.path+'real_file_no_headers.ofx').read())
        OFX = parser.parse()
        try:
            print OFX.BANKMSGSRSV1.notag
        except AttributeError, msg:
            self.assertTrue(msg.message=="OFX.BANKMSGSRSV1 has no 'notag' child node.")
        except :
            self.fail('unexistent attribute test error' )


    def test_06_parse_real_file_as_token_list(self):
        """
        Parse a real file
        """
        parser = OFXParser(open(self.path+'real_file_no_headers.ofx').read())
        print
        tag = parser._OFXParser__read_tag()
        while tag is not None:
            print "%-20s|%-20s|%s " % (tag.get_type_name(), tag.name, tag.value )
            tag = parser._OFXParser__read_tag()


    def test_07_parse_ofx_headers_only(self):
        """
        Parse a real file and extract headers
        """
        parser = OFXParser(open(self.path+'real_file_with_headers.ofx','U').read())
        parser.parse_headers()
        print "\nTest 7: Dumping headers:"
        for h in parser.OFX_headers.items():
            print "-",h
        self.assertTrue(parser.OFX_headers['VERSION']=='102')
        self.assertTrue(parser.OFX_headers['CHARSET']=='1252')


    def test_08_parse_ofx_headers_then_content(self):
        """
        Open a real file, parse headers, then content
        """
        parser = OFXParser(open(self.path+'real_file_with_headers.ofx','U').read())
        parser.parse_headers()
        OFX = parser.parse()
        print "\nTest 8: parse headers then content:"
        self.assertTrue(parser.OFX_headers['VERSION']=='102')
        self.assertTrue(parser.OFX_headers['CHARSET']=='1252')
        self.assertTrue( OFX.BANKMSGSRSV1.STMTTRNRS.TRNUID.val == '41425367824' )


    def test_09_parse_then_inspect_headers_then_content(self):
        """
        Open a real file, parse it, then inspect headers, then content
        """
        parser = OFXParser(open(self.path+'real_file_with_headers.ofx','U').read())
        OFX = parser.parse()
        print "\nTest 9: parse then inspect headers and content:"
        self.assertTrue(parser.OFX_headers['VERSION']=='102')
        self.assertTrue(parser.OFX_headers['CHARSET']=='1252')
        self.assertTrue( OFX.BANKMSGSRSV1.STMTTRNRS.TRNUID.val == '41425367824' )



if __name__=="__main__":
    unittest.main()
    
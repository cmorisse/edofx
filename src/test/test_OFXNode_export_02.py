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

    def test_06_parse_real_file_and_render_as_ofx(self):
        '''
        Parse a real file
        '''
        parser = OFXParser(open(self.path+'real_file.ofx').read())
        ofx_tree = parser.parse()
        
        print ofx_tree.ofx_repr()

    def test_07_parse_real_file_and_render_as_xml(self):
        '''
        Parse a real file
        '''
        parser = OFXParser(open(self.path+'real_file.ofx').read())
        ofx_tree = parser.parse()
        
        print ofx_tree.xml_repr()

    def test_08_parse_real_file(self):
        '''
        Parse a real file
        '''
        parser = OFXParser(open(self.path+'real_file.ofx').read())
        OFX = parser.parse()
        sl = render_as_DOT(OFX)
        print
        for e in sl:
            print e.export_as_csv()

    def test_09_parse_multi_acct_file_and_export_as_xml(self):
        '''
        Parse a real file
        '''
        src = open(self.path+'multi_account_file.ofx')
        parser = OFXParser(src.read())
        src.close()
        
        OFX = parser.parse()

        f = open('output/test_09_output_as_xml.xml','w')
        f.write(OFX.xml_repr())
        f.close()

    def test_10_parse_realfile_and_re_export_it_as_ofx(self):
        '''
        Parse a real file and export it again as OFX
        
        Use a file diff tool to compare test_10_output_as_ofx.ofx with real_file.ofx
        
        On Unix/MacOS files should be identical.
        On Windows, we may have CR/LF differences. 
        
        '''
        src = open(self.path+'real_file.ofx')
        parser = OFXParser(src.read())
        src.close()
        
        OFX = parser.parse()

        f = open('output/test_12_output_as_ofx.ofx','w')
        f.write(OFX.ofx_repr())
        f.close()


    def test_11_parse_multi_acct_file_and_export_as_several_csv(self):
        '''
        Parse a real file and export as many individual csv files
        '''
        src = open(self.path+'multi_account_file.ofx')
        parser = OFXParser(src.read())
        src.close()
        
        OFX = parser.parse()

        statement_list = render_as_DOT(OFX)

        for e in statement_list:
            file_name =  'output/'+e.account_id.strip()+'_statement from_'+str(e.start_date)+'_to_'+str(e.end_date)+'.csv'
            f = open(file_name,'w')
            f.write(e.export_as_csv())
            f.close()
            print e.export_as_csv()            

 

if __name__=="__main__":
    unittest.main()
    
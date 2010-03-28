# coding: utf-8
#
# Copyright (c) 2010 <Cyril MORISSE - cyril.morisse@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
#  * The above copyright notice and this permission notice shall be included in all copies or 
#    substantial portions of the Software.
# 
#  * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#    PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
#    FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
'''
edofx is a library and a DSL to manipulate (mainly read) OFX files.

Created on 28 févr. 2010

@author: Cyril MORISSE - cyril.morisse@gmail.com

'''
import logging
import os
import random

from datetime import date
#
# ofx
#    statement_list[]
#        Statement
#            type = (CHECKING, CREDIT_CARD, INVESTMENT)
#            account_number
#            start_date
#            end_date
#            transaction_list[]
#                StatementTransaction
#            balance
#            balance_date
#
# parser pipeline
# first parse everything as OFX
#
    
class OFXNode(object):
    '''
    Use as a generic way to store file content
    '''
    TYPE_UNDEFINED  = 0
    TYPE_OPENING    = 1
    TYPE_CLOSING    = 2
    TYPE_SELFCLOSING= 3
    TYPE_ERROR      = 9

    def __init__(self, type=TYPE_UNDEFINED, name='', value=''):
        self.logger = logging.getLogger('OFXNode')
        self.type = type
        self.name = name
        self.value = value
        self.children = []
        self.parent = None
        self.__iter_src__=[]
    
    def __get_nodes_chain(self):
        if self.parent == None :
            return self.name
        return self.parent.__get_nodes_chain()+'.'+self.name
    
    def __getattr__(self, name):
        self.logger.info('%s.__getattr__(%s)' % ( self.__get_nodes_chain(), name ) )
        for c in self.children:
            if c.name == name :
                c.parent = self
                return c
        raise AttributeError, "%s has no '%s' child node."  % (self.__get_nodes_chain(), name)

    def __delattr__(self,name):
        self.logger.info('%s.__delattr__(%s)' % ( self.__get_nodes_chain(), name ) )
        delete_list = []
        for c in self.children:
            if c.name == name :
                delete_list.append(c)
        if delete_list:
            while delete_list:
                self.children.__delitem__(self.children.index(delete_list[0]))
                delete_list.__delitem__(0)
            return
        raise AttributeError, "%s has no '%s' child node."  % (self.__get_nodes_chain(), name)
    
    def __build_iter_source(self):
        if self.parent == None:
            return []
        
        for elem in self.parent.children:
            if elem.name == self.name:
                self.__iter_src__.append(elem)
        return self.__iter_src__
    
    def __iter__(self):
        self.logger.info('%s.__iter__' % ( self.__get_nodes_chain() ) )
        if self.__iter_src__:
            return iter(self.__iter_src__)
        return iter(self.__build_iter_source())
    
    def __getitem__(self, index):
        self.logger.info('%s.__getitem__(%i)' % ( self.__get_nodes_chain(), index ) )
        if type(index)==int:
            if self.__iter_src__:
                return self.__iter_src__[index]
            return self.__build_iter_source()[index]
        raise TypeError, "list indices must be integers"

    def __len__(self):
        self.logger.info('%s.__len__()' % ( self.__get_nodes_chain(), ) )
        if self.__iter_src__:
            return len(self.__iter_src__)            
        return len(self.__build_iter_source())

    def __repr__(self, show_parent=False, xml_style=False ):
        if self.value:
            if show_parent :
                return '<%s parent="%s">%s' % (self.name, self.parent.name, self.value,)
            if xml_style:
                return '<%s>%s</%s>' % (self.name, self.value,self.name)
            return '<%s>%s' % (self.name, self.value,)
        return '<%s>...</%s>' % (self.name, self.name,)

    def __val(self):
        if self.name[:2] == 'DT' :
            return date( int(self.value[:4]), int(self.value[4:6]), int(self.value[6:8]) ) 
        elif self.name[-3:] == 'AMT' :
            return float(self.value)
        return self.value
    val = property(__val)
         
    def ofx_repr(self, repr=''):
        if self.value:
            # this is a self closing tag
            return self.__repr__()+'\n'

        repr += "<%s>\n" % self.name
        for c in self.children:
            repr += c.ofx_repr() 
        repr += "</%s>\n" % self.name
        return repr

    def __obfuscate_value(self):
        result = ''
        for c in self.value:
            if c.isalpha() :
                result+=chr(random.randint(65,89))
            elif c.isdigit():
                result+=random.choice('0123456789')
            else:
                result+=c
        return '<%s>%s' % (self.name, result,)

    def obfuscated_ofx_repr(self, repr=''):
        ''' 
        obfuscates output but OFXNode is left unmodified'
        
        Nodes 'ACCTTYPE', 'CODE', 'STATUS', 'SEVERITY', 'LANGUAGE', 
        'CURDEF', 'TRNTYPE' are not obfuscated.
        
        '''
        # TODO: implement a delegate
        if self.value:
            if self.name[:2] == "DT" or self.name in ('ACCTTYPE', 'CODE', 'STATUS', 'SEVERITY', 'LANGUAGE', 'CURDEF', 'TRNTYPE', ) :
                return self.__repr__()+'\n'
            elif self.name[-3:] == 'AMT':
                # TODO: we must return a random float value with the same sign and in a coherent range
                tmp_val = random.random()*1000
                if self.val < 0 :
                    tmp_val = tmp_val * -1
                return '<%s>%.2f\n' % (self.name, tmp_val)

            return self.__obfuscate_value()+'\n'

        repr += "<%s>\n" % self.name
        for c in self.children:
            repr += c.obfuscated_ofx_repr() 
        repr += "</%s>\n" % self.name
        return repr

    def xml_repr(self, indent='', repr=''):
        if self.value:
            # this is a self closing tag
            return indent+self.__repr__(xml_style=True)+'\n'

        repr += indent+"<%s>\n" % self.name
        for c in self.children:
            repr += c.xml_repr(indent+'    ') 
        repr += indent+"</%s>\n" % self.name
        return repr

    def find_children_by_name(self, search_name):
        '''
            returns a list of all subnodes named after search_name
        '''
        if self.name == search_name:
            return [self]
        found_list = []  
        for n in self.children:
            found_list.extend(n.find_children_by_name(search_name))
        return found_list
    
    def get_type_name(self):
        ''' 
        Used for parser tuning
        '''
        if self.type == self.TYPE_UNDEFINED:
            return 'TYPE_UNDEFINED'
        elif self.type == self.TYPE_OPENING:
            return 'TYPE_OPENING'
        elif self.type == self.TYPE_CLOSING:
            return 'TYPE_CLOSING'
        elif self.type == self.TYPE_SELFCLOSING:
            return 'TYPE_SELFCLOSING'
        elif self.type == self.TYPE_ERROR:
            return 'TYPE_ERROR'

class OFXParser(object):
    '''
    Parses an OFX source string and returns corresponding OFXNode tree
    '''
    def __init__(self, source):
        '''
        setup parser and define parsing parameters.
        '''
        self.logger = logging.getLogger('OFXParser')
        
        if len(source) < 10:
            self.logger.error("Supplied source string is null")
            self.ready = False
            self.src = ""

        self.ready               = True
        self.source              = source
        self.source_idx          = 0
        self.source_len          = len(source)
        self.__EOF               = False
        self.current_char        = None
        self.current_line_number = 1
        self.OFX_tree            = None
        
    def __read_char(self):
        '''
        Consume one char from source.
        Sets __EOF when end of file has been reached.
        Returns '' on EOF.
        
        '''
        if self.__EOF:
            return ''
        
        self.current_char = self.source[self.source_idx]
        self.source_idx+=1
        
        if self.current_char == '\n' :
            self.current_line_number +=1
        
        if self.source_idx==self.source_len:
            self.__EOF=True
            
        return self.current_char

    def __reject_char(self):
        '''
        Rewind one char from source and return it.
        
        '''
        self.source_idx-=1
        self.__EOF=False
        self.current_char = self.source[self.source_idx]            
        return self.current_char

    def __read_tag_name(self, first_char=''):
        '''
        Read an OFX tag name (Uppercase and Letters string)
        
        '''
        c = self.__read_char()
        tmp_name = first_char
        while(c<>'' and c<>'>'):
            tmp_name += c
            c = self.__read_char()
        
        if c=='' :
            # we should not have encountered eof in a tag name
            return ''
        
        if not tmp_name.isalpha() and not tmp_name.isupper() :
            return ''
        
        return tmp_name    
        
    def __read_tag_value(self,first_char=''):
        '''
        Read an OFX tag value 
            Tag value starts after the tag until beginning of next tag
            Tag value can't spawn several lines        
        '''
        c = self.__read_char()
        tmp_name = first_char
        while( c <> '<' ):
            tmp_name += c
            c = self.__read_char()
        
        if c=='<' :
            return tmp_name # may be we should not accept a selfclosing tag alone
        
        if c == '\r' :
            # if we have \n after it's ok ; this is a PC generated file
            # else this is a file error
            c = self.__read_char()
            if c == '\n' :
                return tmp_name
            else:
                # log : malformed end of line
                return None

        if c == '\n' :
            # only \n after a tag is ok ; this is a Unix generated file
            return tmp_name    

        return None # should never pass here

    def __read_tag(self):
        '''
        parse current file and return one tag.
        
        returns:
            None when EOF is reached
            Tag with type = TYPE_ERROR if line is malformed
        '''
                
        #current_tag = Tag()
        current_tag = OFXNode()

        c = self.__read_char()

        if(c=='<'):
            c = self.__read_char()
            if( c==''):
                current_tag.type = OFXNode.TYPE_ERROR
                return current_tag

            if( c=='/'):    # CLOSING TAG
                current_tag.type = OFXNode.TYPE_CLOSING
                current_tag.name = self.__read_tag_name()  
            else:           # OPENING or SELF_CLOSING TAG
                current_tag.name = self.__read_tag_name(c) 
            # Note : read_tag_name consumes trailing '>'

            if current_tag.name == '':
                current_tag.type = OFXNode.TYPE_ERROR
                return current_tag
            
            tmp_value = ''
            value = False
            c = self.__read_char()
            while c <> '<' and c <> '' :
                tmp_value += c
                if c <> '\r' and c <> '\n' :
                    value = True
                c = self.__read_char()

            # we reject '<' we've just read
            self.__reject_char()
            
            # type ==  TYPE_CLOSING and value = False     => TYPE_CLOSING
            # type ==  TYPE_CLOSING and value             => TYPE_ERROR
            # type <>  TYPE_CLOSING and value == False    => TYPE_OPENING      mais incohérent avec le EOF 
            # type <>  TYPE_CLOSING and value == True     => TYPE_SELFCLOSING  mais incohérent avec le EOF
            
            if current_tag.type == OFXNode.TYPE_CLOSING:
                if value:
                    current_tag.type = OFXNode.TYPE_ERROR
                return current_tag

            if value :
                current_tag.type = OFXNode.TYPE_SELFCLOSING
                if tmp_value[-1]=='\n' and tmp_value[-2]=='\r': # PC end of line
                    current_tag.value = tmp_value[:-2]  
                elif tmp_value[-1] == '\n' :                    # Unix style end of line
                    current_tag.value = tmp_value[:-1]
                else :
                    current_tag.value = tmp_value
            else :
                current_tag.type = OFXNode.TYPE_OPENING
                    
            return current_tag


    def __parse(self):
        
        tag = self.__read_tag()
        if tag.type == tag.TYPE_CLOSING :
            return None

        if tag.type == tag.TYPE_SELFCLOSING :
            return tag
        
        child = self.__parse()
        while child <> None :
            tag.children.append( child )
            child = self.__parse()
        
        return tag

    def set_source(self, source):
        
        if len(source) < 10:
            self.logger.error("Supplied source string is null")
            self.ready = False
            self.src = ''

        self.source              = source
        self.source_idx          = 0
        self.source_len          = len(source)
        self.ready               = True
        self.__EOF               = False
        self.current_char        = None
        self.current_line_number = 1
        self.OFX_tree            = None
    
    def parse(self):
        '''
        Parse OFX source and returns an OFXNode tree
        
        return None if source is undefined.
        '''
        if not self.ready:
            return None

        if self.OFX_tree <> None: 
            return self.OFX_tree
        
        self.OFX_tree = self.__parse()

        return self.OFX_tree

class OFXObfuscator(object):
    '''
    Obfuscates OFX source strings
    
    Problem with OFXObfuscator is that it's so basic, it breaks date.
    So when parsing an obfuscated file you can't use .val on date attribute
    an must rely on .value. 
    
    '''
    def __init__(self, source):
        '''
        setup parser and define parsing parameters.
        '''
        self.logger = logging.getLogger('OFXObfuscator')
        
        if len(source) < 10:
            self.logger.error("Supplied source string is too short to be an OFX")
            self.ready = False
            self.source = ""

        self.ready      = True
        self.source     = source
        self.source_idx = 0
        self.source_len = len(source)
        self.result     = ''

    def __read_tag_name(self):
        '''
        Read an OFX tag name (Uppercase and Letters string)
        
        '''
        # on entry idx is on '<'
        # on exit idx is on '>'
        while self.source_idx < self.source_len and self.source[self.source_idx] <> '>' :
            self.result += self.source[self.source_idx]
            self.source_idx+=1
        
        if self.source_idx < self.source_len:
            self.result += self.source[self.source_idx]
                    
    def obfuscate(self):
        if not self.ready:
            raise "NotReady"
        
        while( self.source_idx < self.source_len ) :
            
            current_char = self.source[self.source_idx]
            
            if current_char == '<' :
                self.result+= '<'
                self.source_idx+=1
                self.__read_tag_name()
                
            elif current_char.isdigit() :
                self.result+='9'
            elif current_char.isalpha():
                self.result+= 'A'
            else :
                self.result += current_char

            self.source_idx+=1;
                 
        return self.result

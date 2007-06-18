<?php
/**
 * Record-oriented API for XML.
 *
 * $Horde: framework/XML_RAX/RAX.php,v 1.2 2004/01/20 02:19:51 chuck Exp $
 *
 * @package XML_RAX
 */
class XML_RAX {

    var $_record = '';
    var $_fields = array();
    var $_records = array();
    var $_parser;
    var $_inRecord = false;
    var $_inField = false;
    var $_fieldData = '';
    var $_tags = array();
    var $_xml = '';
    var $_xmlFp;
    var $_opened = false;
    var $_initialized = false;
    var $_finished = false;

    function XML_RAX()
    {
    }

    function open($xml)
    {
        if ($this->_opened) {
            return false;
        }

        $this->_xml = $xml;
        $this->_opened = true;
    }

    function openfile($filename)
    {
        if ($this->_opened) {
            return false;
        }

        $fp = fopen($filename, 'r');
        if ($fp) {
            $this->_xmlFp = $fp;
            $this->_opened = true;
            return true;
        }

        return false;
    }

    function parse()
    {
        if (!$this->_opened) {
            return false;
        }

        if ($this->_finished) {
            return false;
        }

        if (!$this->_initialized) {
            if (!$this->_init()) {
                return false;
            }
        }

        if ($this->_xmlFp) {
            $buffer = fread($this->_xmlFp, 4096);
            if ($buffer) {
                xml_parse($this->_parser, $buffer, feof($this->_xmlFp));
            } else {
                $this->_finished = true;
            }
        } else {
            xml_parse($this->_parser, $this->_xml, 1);
            $this->_finished = true;
        }
        return true;
    }

    function setRecord($record)
    {
        if ($this->_initialized) {
            return false;
        }
        $this->_record = $record;
        return true;
    }

    function readRecord()
    {
        while (!count($this->_records) && !$this->_finished) {
            $this->parse();
        }
        return array_shift($this->_records);
    }

    function _init()
    {
        $this->_parser = xml_parser_create();
        xml_set_object($this->_parser, $this);
        xml_set_element_handler($this->_parser, '_start', '_end');
        xml_set_character_data_handler($this->_parser, '_data');
        xml_parser_set_option($this->_parser, XML_OPTION_CASE_FOLDING, 0);
        if (xml_parse($this->_parser, '')) {
            $this->_initialized = true;
            return true;
        }

        return false;
    }

    function _start($parser, $name, $attrs)
    {
        array_push($this->_tags, $name);
        if (!$this->_inRecord && !strcmp($name, $this->_record)) {
            $this->_inRecord = 1;
            $this->_rec_lvl = count($this->_tags);
            $this->_field_lvl = $this->_rec_lvl + 1;
        } elseif ($this->_inRecord && count($this->_tags) == $this->_field_lvl) {
            $this->_inField = 1;
        }
    }

    function _end($parser, $name)
    {
        array_pop($this->_tags);
        if ($this->_inRecord) {
            if (count($this->_tags) < $this->_rec_lvl) {
                $this->_inRecord = 0;
                array_push($this->_records, new XML_RAX_Record($this->_fields));
                $this->_fields = array();
            } elseif (count($this->_tags) < $this->_field_lvl) {
                $this->_inField = 0;
                $this->_fields[$name] = $this->_fieldData;
                $this->_fieldData = '';
            }
        }
    }

    function _data($parser, $data)
    {
        if ($this->_inField) {
            $this->_fieldData .= $data;
        }
    }

}

class XML_RAX_Record {

    var $_fields;

    function XML_RAX_Record($fields)
    {
        $this->_fields = $fields;
    }

    function getFieldnames()
    {
        return array_keys($this->_fields);
    }

    function getField($field)
    {
        return isset($this->_fields[$field]) ?
            trim($this->_fields[$field]) :
            null;
    }

    function getFields()
    {
        return array_values($this->_fields);
    }

    function getRow()
    {
        return $this->_fields;
    }

}

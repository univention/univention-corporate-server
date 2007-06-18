<?php
/**
 * $Horde: framework/XML_WBXML/WBXML/ContentHandler.php,v 1.8 2004/01/20 02:21:54 chuck Exp $
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * From Binary XML Content Format Specification Version 1.3, 25 July
 * 2001 found at http://www.wapforum.org
 *
 * @package XML_WBXML
 */
class XML_WBXML_ContentHandler {

    var $_currentUri;
    var $_indent = 0;
    var $_output = '';

    var $_opaqueHandler;

    /**
     * Charset.
     */
    var $_charset = 'UTF-8';

    /**
     * WBXML Version.
     * 1, 2, or 3 supported
     */
    var $_wbxmlVersion = 2;

    function XML_WBXML_ContentHandler()
    {
        $this->_currentUri = &new XML_WBXML_LifoQueue();
    }

    function raiseError($error)
    {
        include_once 'PEAR.php';
        return PEAR::raiseError($error);
    }

    function getCharsetStr()
    {
        return $this->_charset;
    }

    function setCharset($cs)
    {
        $this->_charset = $cs;
    }

    function getVersion()
    {
        return $this->_wbxmlVersion;
    }

    function setVersion($v)
    {
        $this->_wbxmlVersion = 2;
    }

    function getOutput()
    {
        return $this->_output;
    }

    function startElement($uri, $element, $attrs)
    {
        $this->_padspaces();
        $this->_output .= '<' . $element;

        $currentUri = $this->_currentUri->top();

        if ((!$currentUri) || ($currentUri != $uri)) {
            $this->_output .= ' xmlns="' . $uri . '"';
        }

        $this->_currentUri->push($uri);

        foreach ($attrs as $attr) {
            $this->_output .= ' ' . $attr['attiribute'] . '="' . $attr['value'] . '"';
        }

        $this->_output .= ">\n";

        $this->_indent++;
    }

    function endElement($uri, $element)
    {
        $this->_indent--;

        $this->_padspaces();
        $this->_output .= '</' . $element . ">\n";

        $this->_currentUri->pop();
    }

    function characters($str)
    {
        $this->_padspaces();
        $this->_output .= $str . "\n";
    }

    function opaque($o)
    {
        //I can check the first chanracter and see if it is WBXML
        if (ord($o[0]) < 10) {
            //should decode this, I really need a call back function

        } else {
            $this->_output .= $o . "\n";
        }
    }

    /**
     * Padding to make it easier to read.
     */
    function _padspaces()
    {
        if ($this->_indent > 0) {
            $this->_output .= str_repeat(' ', $this->_indent);
        }
    }


    function setOpaqueHandler($opaqueHandler)
    {
        $this->_opaqueHandler = $opaqueHandler;
    }

    function removeOpaqueHandler()
    {
        unset($this->_opaqueHandler);
    }

}

class XML_WBXML_LifoQueue {

    var $_queue = array();

    function XML_WBXML_LifoQueue()
    {
    }

    function push($obj)
    {
        array_push($this->_queue, $obj);
    }

    function pop()
    {
        if (count($this->_queue)) {
            return array_pop($this->_queue);
        } else {
            return null;
        }
    }

    function top()
    {
        if ($count = count($this->_queue)) {
            return $this->_queue[$count - 1];
        } else {
            return null;
        }
    }

}

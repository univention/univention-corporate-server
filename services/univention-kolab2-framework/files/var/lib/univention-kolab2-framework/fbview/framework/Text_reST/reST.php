<?php
/**
 * The Text_reST:: class provides an API for manipulating a
 * reStructuredText document.
 *
 * $Horde: framework/Text_reST/reST.php,v 1.4 2004/01/01 15:14:35 jan Exp $
 *
 * Copyright 2003-2004 Jason M. Felice <jfelice@cronosys.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jfelice@cronosys.com>
 * @version $Revision: 1.1.2.1 $
 * @package Text_reST
 */
class Text_reST {

    /**
     * This is the parse node type.  It is set from the constructor.
     *
     * @access private
     * @var string $_type
     */
    var $_type;

    /**
     * This is an array of the parse node's children.
     *
     * @access private
     * @var string $_children
     */
    var $_children = array();

    /**
     * This is a hash of parse node properties.
     *
     * @access private
     * @var array $_properties
     */
    var $_properties = array();

    /**
     * Construct a new parse node.
     *
     * @access public
     *
     * @param optional string $type     This is the node type.  The default is
     *                                  'Document'.
     */
    function Text_reST($type = 'Document')
    {
        $this->_type = $type;
    }

    /**
     * Append a child parse node to this parse node.
     *
     * @access public
     *
     * @param optional mixed &$child    This is the string or object child
     *                                  to append to this parse node.
     */
    function appendChild(&$child)
    {
        $n = count($this->_children);
        if (is_string($child) && $n > 0 && is_string($this->_children[$n-1])) {
            $this->_children[$n-1] .= $child;
        } elseif (is_string($child)) {
            $this->_children[] = $child;
        } else {
            $this->_children[] = &$child;
        }
    }

    /**
     * Set the value of a parse node property.
     *
     * @param string $name          This is the property's name.
     * @param string $value         This is the property's value.
     */
    function setProperty($name, $value)
    {
        $this->_properties[$name] = $value;
    }

    /**
     * Retreive the value of a parse node property.
     *
     * @param string $name          This is the property's name.
     * @return string the property's value.
     */
    function getProperty($name)
    {
        if (!array_key_exists($name, $this->_properties)) {
            return null;
        }
        return $this->_properties[$name];
    }

    /**
     * Dump this parse node and its children.
     *
     * @access public
     *
     * @param optional int $level       This is the indent level of this
     *                                  parse node.
     */
    function dump($level = 0)
    {
        for ($i = 0; $i < $level; $i++) {
            echo '  ';
        }
        echo $this->_type, '::';
        ksort($this->_properties);
        foreach ($this->_properties as $name => $value) {
            echo ' ', $name, '="', preg_replace('/["\\\\]/', '\\$1', $value),
                '"';
        }
        echo "\n";
        foreach ($this->_children as $child) {
            if (is_string($child)) {
                for ($i = 0; $i < ($level + 1); $i++) {
                    echo '  ';
                }
                echo '"', preg_replace('/["\\\\]/', '\\$1', $child), "\"\n";
            } else {
                $child->dump($level + 1);
            }
        }
    }

    /**
     * Parse a reStructuredText document.
     *
     * @static
     *
     * @param string $text          This is the text of the document we
     *                              want to parse.
     * @return object Text_reST the parsed document or a 
     *      PEAR_Error:: instance if something went wrong.
     */
    function &parse($text)
    {
        require_once dirname(__FILE__) . '/reST/Parser.php';
        $parser = &new Text_reST_Parser();
        return $parser->parse($text);
    }

}


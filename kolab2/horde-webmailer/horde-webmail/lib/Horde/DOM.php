<?php
/**
 * The Horde_DOM_Document and related classes provide a PHP 4 domxml
 * compatible wrapper around the PHP 5 dom implementation to allow scripts
 * written for PHP 4 domxml model to work under PHP 5's dom support.
 *
 * This code was derived from the Horde_Config_Dom and related classes which
 * in turn was derived from code written by Alexandre Alapetite. The only
 * changes made to the original code were to implement Horde's coding
 * standards and some minor changes to more easily fit into the framework.
 * The original code can be found at:
 * http://alexandre.alapetite.net/doc-alex/domxml-php4-php5/
 *
 * $Horde: framework/DOM/DOM.php,v 1.9.2.6 2009-10-14 16:42:35 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_DOM
 */

/** PEAR */
require_once 'PEAR.php';

/** Validate against the DTD */
define('HORDE_DOM_LOAD_VALIDATE', 1);

/** Recover from load errors */
define('HORDE_DOM_LOAD_RECOVER', 2);

/** Remove redundant whitespace */
define('HORDE_DOM_LOAD_REMOVE_BLANKS', 4);

/** Substitute XML entities */
define('HORDE_DOM_LOAD_SUBSTITUTE_ENTITIES', 8);

class Horde_DOM_Document extends Horde_DOM_Node {

    /**
     * Creates an appropriate object based on the version of PHP that is
     * running and the requested xml source. This function should be passed an
     * array containing either 'filename' => $filename | 'xml' => $xmlstring
     * depending on the source of the XML document.
     *
     * You can pass an optional 'options' parameter to enable extra
     * features like DTD validation or removal of whitespaces.
     * For a list of available features see the HORDE_DOM_LOAD defines.
     * Multiple options are added by bitwise OR.
     *
     * @param array $params  Array containing either 'filename' | 'xml' keys.
     *                       You can specify an optional 'options' key.
     *
     * @return mixed   PHP 4 domxml document | Horde_DOM_Document | PEAR_Error
     */
    function factory($params = array())
    {
        if (!isset($params['options'])) {
            $params['options'] = 0;
        }

        if (version_compare(PHP_VERSION, '5', '>=')) {
            // PHP 5 with Horde_DOM. Let Horde_DOM determine
            // if we are a file or string.
            $doc = new Horde_DOM_Document($params);
            if (isset($doc->error)) {
                return $doc->error;
            }
            return $doc;
        }

        // Load mode
        if ($params['options'] & HORDE_DOM_LOAD_VALIDATE) {
            $options = DOMXML_LOAD_VALIDATING;
        } elseif ($params['options'] & HORDE_DOM_LOAD_RECOVER) {
            $options = DOMXML_LOAD_RECOVERING;
        } else {
            $options = DOMXML_LOAD_PARSING;
        }

        // Load options
        if ($params['options'] & HORDE_DOM_LOAD_REMOVE_BLANKS) {
            $options |= DOMXML_LOAD_DONT_KEEP_BLANKS;
        }
        if ($params['options'] & HORDE_DOM_LOAD_SUBSTITUTE_ENTITIES) {
            $options |= DOMXML_LOAD_SUBSTITUTE_ENTITIES;
        }

        if (isset($params['filename'])) {
            if (function_exists('domxml_open_file')) {
                // PHP 4 with domxml and XML file
                return domxml_open_file($params['filename'], $options);
            }
        } elseif (isset($params['xml'])) {
            if (function_exists('domxml_open_mem')) {
                // PHP 4 with domxml and XML string.
                $result = @domxml_open_mem($params['xml'], $options);
                if (!$result) {
                    return PEAR::raiseError('Failed loading XML document.');
                }
                return $result;
            }
        } elseif (function_exists('domxml_new_doc')) {
            // PHP 4 creating a blank doc.
            return domxml_new_doc('1.0');
        }

        // No DOM support - raise error.
        return PEAR::raiseError('DOM support not present.');
    }

    /**
     * Constructor.  Determine if we are trying to load a file or xml string
     * based on the parameters.
     *
     * @param array $params  Array with key 'filename' | 'xml'
     */
    function Horde_DOM_Document($params = array())
    {
        $this->node = new DOMDocument();

        // Load mode
        if ($params['options'] & HORDE_DOM_LOAD_VALIDATE) {
            $this->node->validateOnParse = true;
        } elseif ($params['options'] & HORDE_DOM_LOAD_RECOVER) {
            $this->node->recover = true;
        }

        // Load options
        if ($params['options'] & HORDE_DOM_LOAD_REMOVE_BLANKS) {
            $this->node->preserveWhiteSpace = false;
        }
        if ($params['options'] & HORDE_DOM_LOAD_SUBSTITUTE_ENTITIES) {
            $this->node->substituteEntities = true;
        }

        if (isset($params['xml'])) {
            $result = @$this->node->loadXML($params['xml']);
            if (!$result) {
                $this->error = PEAR::raiseError('Failed loading XML document.');
                return;
            }
        } elseif (isset($params['filename'])) {
            $this->node->load($params['filename']);
        }
        $this->document = $this;
    }

    /**
     * Return the root document element.
     */
    function root()
    {
        return new Horde_DOM_Element($this->node->documentElement, $this);
    }

    /**
     * Return the document element.
     */
    function document_element()
    {
        return $this->root();
    }

    /**
     * Return the node represented by the requested tagname.
     *
     * @param string $name  The tagname requested.
     *
     * @return array The nodes matching the tag name
     */
    function get_elements_by_tagname($name)
    {
        $list = $this->node->getElementsByTagName($name);
        $nodes = array();
        $i = 0;
        if (isset($list)) {
            while ($node = $list->item($i)) {
                $nodes[] = $this->_newDOMElement($node, $this);
                ++$i;
            }
            return $nodes;
        }
    }

    /**
     * Return the document as a text string.
     *
     * @param bool   $format    Specifies whether the output should be
     *                          neatly formatted, or not
     * @param string $encoding  Sets the encoding attribute in line
     *                          <?xml version="1.0" encoding="iso-8859-1"?>
     *
     * @return string The xml document as a string
     */
    function dump_mem($format = false, $encoding = false)
    {
        $format0 = $this->node->formatOutput;
        $this->node->formatOutput = $format;

        $encoding0 = $this->node->encoding;
        if ($encoding) {
            $this->node->encoding=$encoding;
        }

        $dump = $this->node->saveXML();

        $this->node->formatOutput = $format0;

        // UTF-8 is the default encoding for XML.
        if ($encoding) {
            $this->node->encoding = $encoding0 == '' ? 'UTF-8' : $encoding0;
        }

        return $dump;
    }

    /**
     * Create a new element for this document
     *
     * @param string $name  Name of the new element
     *
     * @return Horde_DOM_Element  New element
     */
    function create_element($name)
    {
        return new Horde_DOM_Element($this->node->createElement($name), $this);
    }

    /**
     * Create a new text node for this document
     *
     * @param string $content  The content of the text element
     *
     * @return Horde_DOM_Node  New node
     */
    function create_text_node($content)
    {
        return new Horde_DOM_Text($this->node->createTextNode($content), $this);
    }

    /**
     * Create a new attribute for this document
     *
     * @param string $name   The name of the attribute
     * @param string $value  The value of the attribute
     *
     * @return Horde_DOM_Attribute  New attribute
     */
    function create_attribute($name, $value)
    {
        $attr = $this->node->createAttribute($name);
        $attr->value = $value;
        return new Horde_DOM_Attribute($attr, $this);
    }

    function xpath_new_context()
    {
        return Horde_DOM_XPath::factory($this->node);
    }
}

/**
 * @package Horde_DOM
 */
class Horde_DOM_Node {

    var $node;
    var $document;

    /**
     * Wrap a DOMNode into the Horde_DOM_Node class.
     *
     * @param DOMNode            $node      The DOMXML node
     * @param Horde_DOM_Document $document  The parent document
     *
     * @return Horde_DOM_Node  The wrapped node
     */
    function Horde_DOM_Node($domNode, $domDocument = null)
    {
        $this->node = $domNode;
        $this->document = $domDocument;
    }

    function __get($name)
    {
        switch ($name) {
        case 'type':
            return $this->node->nodeType;

        case 'tagname':
            return $this->node->tagName;

        case 'content':
            return $this->node->textContent;

        default:
            return false;
        }
    }

    /**
     * Set the content of this node.
     *
     * @param string $text The new content of this node.
     *
     * @return DOMNode  The modified node.
     */
    function set_content($text)
    {
        return $this->node->appendChild($this->node->ownerDocument->createTextNode($text));
    }

    /**
     * Return the type of this node.
     *
     * @return integer  Type of this node.
     */
    function node_type()
    {
        return $this->node->nodeType;
    }

    function child_nodes()
    {
        $nodes = array();

        $nodeList = $this->node->childNodes;
        if (isset($nodeList)) {
            $i = 0;
            while ($node = $nodeList->item($i)) {
                $nodes[] = $this->_newDOMElement($node, $this->document);
                ++$i;
            }
        }

        return $nodes;
    }

    /**
     * Return the attributes of this node.
     *
     * @return array  Attributes of this node.
     */
    function attributes()
    {
        $attributes = array();

        $attrList = $this->node->attributes;
        if (isset($attrList)) {
            $i = 0;
            while ($attribute = $attrList->item($i)) {
                $attributes[] = new Horde_DOM_Attribute($attribute, $this->document);
                ++$i;
            }
        }

        return $attributes;
    }

    function first_child()
    {
        return $this->_newDOMElement($this->node->firstChild, $this->document);
    }

    /**
     * Return the content of this node.
     *
     * @return string  Text content of this node.
     */
    function get_content()
    {
        return $this->node->textContent;
    }

    function has_child_nodes()
    {
        return $this->node->hasChildNodes();
    }

    function next_sibling()
    {
        if ($this->node->nextSibling === null) {
            return null;
        }

        return $this->_newDOMElement($this->node->nextSibling, $this->document);
    }

    function node_value()
    {
        return $this->node->nodeValue;
    }

    function node_name()
    {
        if ($this->node->nodeType == XML_ELEMENT_NODE) {
            return $this->node->localName;
        } else {
            return $this->node->nodeName;
        }
    }

    function clone_node()
    {
        return new Horde_DOM_Node($this->node->cloneNode());
    }

    /**
     * Append a new node
     *
     * @param Horde_DOM_Node $newnode  The child to be added
     *
     * @return Horde_DOM_Node  The resulting node
     */
    function append_child($newnode)
    {
        return $this->_newDOMElement($this->node->appendChild($this->_importNode($newnode)), $this->document);
    }

    /**
     * Remove a child node
     *
     * @param Horde_DOM_Node $oldchild  The child to be removed
     *
     * @return Horde_DOM_Node  The resulting node
     */
    function remove_child($oldchild)
    {
        return $this->_newDOMElement($this->node->removeChild($oldchild->node), $this->document);
    }

    /**
     * Return a node of this class type.
     *
     * @param DOMNode            $node      The DOMXML node
     * @param Horde_DOM_Document $document  The parent document
     *
     * @return Horde_DOM_Node  The wrapped node
     */
    function _newDOMElement($node, $document)
    {
        if ($node == null) {
            return null;
        }

        switch ($node->nodeType) {
        case XML_ELEMENT_NODE:
            return new Horde_DOM_Element($node, $document);
        case XML_TEXT_NODE:
            return new Horde_DOM_Text($node, $document);
        case XML_ATTRIBUTE_NODE:
            return new Horde_DOM_Attribute($node, $document);
        // case XML_PI_NODE:
        //     return new Horde_DOM_ProcessingInstruction($node, $document);
        default:
            return new Horde_DOM_Node($node, $document);
        }
    }

    /**
     * Private function to import DOMNode from another DOMDocument.
     *
     * @param Horde_DOM_Node  $newnode The node to be imported
     *
     * @return Horde_DOM_Node  The wrapped node
     */
    function _importNode($newnode)
    {
        if ($this->document === $newnode->document) {
            return $newnode->node;
        } else {
            return $this->document->node->importNode($newnode->node, true);
        }
    }

}

/**
 * @package Horde_DOM
 */
class Horde_DOM_Element extends Horde_DOM_Node {

    /**
     * Get the value of specified attribute.
     *
     * @param string $name  Name of the attribute
     *
     * @return string  Indicates if the attribute was set.
     */
    function get_attribute($name)
    {
        return $this->node->getAttribute($name);
    }

    /**
     * Determine if an attribute of this name is present on the node.
     *
     * @param string $name Name of the attribute
     *
     * @return bool  Indicates if such an attribute is present.
     */
    function has_attribute($name)
    {
        return $this->node->hasAttribute($name);
    }

    /**
     * Set the specified attribute on this node.
     *
     * @param string $name  Name of the attribute
     * @param string $value The new value of this attribute.
     *
     * @return mixed  Indicates if the attribute was set.
     */
    function set_attribute($name, $value)
    {
        return $this->node->setAttribute($name, $value);
    }

    /**
     * Return the node represented by the requested tagname.
     *
     * @param string $name  The tagname requested.
     *
     * @return array The nodes matching the tag name
     */
    function get_elements_by_tagname($name)
    {
        $list = $this->node->getElementsByTagName($name);
        $nodes = array();
        $i = 0;
        if (isset($list)) {
            while ($node = $list->item($i)) {
                $nodes[] = $this->_newDOMElement($node, $this->document);
                $i++;
            }
        }

        return $nodes;
    }

}

/**
 * @package Horde_DOM
 */
class Horde_DOM_Attribute extends Horde_DOM_Node {

    /**
     * Return a node of this class type.
     *
     * @param DOMNode             $node      The DOMXML node
     * @param Horde_DOM_Document  $document  The parent document
     *
     * @return Horde_DOM_Attribute  The wrapped attribute
     */
    function _newDOMElement($node, $document)
    {
        return new Horde_DOM_Attribute($node, $document);
    }

}

/**
 * @package Horde_DOM
 */
class Horde_DOM_Text extends Horde_DOM_Node {

    function __get($name)
    {
        if ($name == 'tagname') {
            return '#text';
        } else {
            return parent::__get($name);
        }
    }

    function tagname()
    {
        return '#text';
    }

    /**
     * Set the content of this node.
     *
     * @param string $text  The new content of this node.
     */
    function set_content($text)
    {
        $this->node->nodeValue = $text;
    }

}

/**
 * @package Horde_DOM
 */
class Horde_DOM_XPath {

    /**
     * @var DOMXPath
     */
    var $_xpath;

    function factory($dom)
    {
        if (version_compare(PHP_VERSION, '5', '>=')) {
            // PHP 5 with Horde_DOM.
            return new Horde_DOM_XPath($dom);
        }

        return $dom->xpath_new_context();
    }

    function Horde_DOM_XPath($dom)
    {
        $this->_xpath = new DOMXPath($dom);
    }

    function xpath_register_ns($prefix, $uri)
    {
        $this->_xpath->registerNamespace($prefix, $uri);
    }

    function xpath_eval($expression, $context = null)
    {
        if (is_null($context)) {
            $nodeset = $this->_xpath->query($expression);
        } else {
            $nodeset = $this->_xpath->query($expression, $context);
        }
        $result = new stdClass();
        $result->nodeset = array();
        for ($i = 0; $i < $nodeset->length; $i++) {
            $result->nodeset[] = new Horde_DOM_Element($nodeset->item($i));
        }
        return $result;
    }

}

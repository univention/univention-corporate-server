<?php
/**
 * $Horde: framework/Xml_Element/lib/Horde/Xml/Element.php,v 1.2.2.6 2009-01-06 15:23:50 jan Exp $
 *
 * Portions Copyright 2005-2007 Zend Technologies USA Inc. (http://www.zend.com)
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @category Horde
 * @package Horde_Xml_Element
 */

/**
 * Wraps a DOMElement allowing for SimpleXML-like access to attributes.
 *
 * @method mixed TAGNAME() To get the un-wrapped value of a node, use
 * method syntax ($xml_element->tagname()). This will return the
 * string value of the tag if it is a single tag, an array of
 * Horde_Xml_Element objects if there are multiple tags, or null if
 * the tag does not exist.
 *
 * @category Horde
 * @package Horde_Xml_Element
 */
class Horde_Xml_Element implements ArrayAccess {

    /**
     * @var array
     */
    protected static $_namespaces = array(
        'opensearch' => 'http://a9.com/-/spec/opensearchrss/1.0/',
        'atom' => 'http://www.w3.org/2005/Atom',
        'rss' => 'http://blogs.law.harvard.edu/tech/rss',
    );

    /**
     * Get the full version of a namespace prefix
     *
     * Looks up a prefix (atom:, etc.) in the list of registered
     * namespaces and returns the full namespace URI if
     * available. Returns the prefix, unmodified, if it's not
     * registered.
     *
     * @return string
     */
    public static function lookupNamespace($prefix)
    {
        return isset(self::$_namespaces[$prefix]) ?
            self::$_namespaces[$prefix] :
            $prefix;
    }

    /**
     * Add a namespace and prefix to the registered list
     *
     * Takes a prefix and a full namespace URI and adds them to the
     * list of registered namespaces for use by
     * Horde_Xml_Element::lookupNamespace().
     *
     * @param string $prefix The namespace prefix
     * @param string $namespaceURI The full namespace URI
     */
    public static function registerNamespace($prefix, $namespaceURI)
    {
        self::$_namespaces[$prefix] = $namespaceURI;
    }

    /**
     * @var DOMElement
     */
    protected $_element;

    /**
     * A string representation of the element, used when
     * serializing/unserializing.
     *
     * @var string
     */
    protected $_serialized;

    /**
     * @var Horde_Xml_Element
     */
    protected $_parentElement;

    /**
     * @var boolean
     */
    protected $_appended = true;

    /**
     * Horde_Xml_Element constructor.
     *
     * @param DOMElement $element The DOM element we're encapsulating.
     */
    public function __construct($element = null)
    {
        $this->_element = $element;
        $this->__wakeup();
    }

    /**
     * Get a DOM representation of the element
     *
     * Returns the underlying DOM object, which can then be
     * manipulated with full DOM methods.
     *
     * @return DOMDocument
     */
    public function getDom()
    {
        return $this->_element;
    }

    /**
     * Update the object from a DOM element
     *
     * Take a DOMElement object, which may be originally from a call
     * to getDom() or may be custom created, and use it as the
     * DOM tree for this Horde_Xml_Element.
     *
     * @param DOMElement $element
     */
    public function setDom(DOMElement $element)
    {
        $this->_element = $this->_element->ownerDocument->importNode($element, true);
    }

    /**
     * Add child elements and attributes to this element from a simple
     * key => value hash. Keys can be:
     *
     *   ElementName               -> <$ElementName> will be appended with
     *                                a value of $value
     *   #AttributeName            -> An attribute $AttributeName will be
     *                                added to this element with a value
     *                                of $value
     *   ElementName#AttributeName -> <$ElementName> will be appended to this
     *                                element if it doesn't already exist,
     *                                and have its attribute $AttributeName
     *                                set to $value
     *
     * @param $array Hash to import into this element.
     */
    public function fromArray($array)
    {
        foreach ($array as $key => $value) {
            $element = null;
            $attribute = null;

            $hash_position = strpos($key, '#');
            if ($hash_position === false) {
                $element = $key;
            } elseif ($hash_position === 0) {
                $attribute = substr($key, 1);
            } else {
                list($element, $attribute) = explode('#', $key, 2);
            }

            if (!is_null($element)) {
                if (!is_null($attribute)) {
                    $this->{$element}[$attribute] = $value;
                } else {
                    if (is_array($value)) {
                        $this->$element->fromArray($value);
                    } else {
                        $this->$element = $value;
                    }
                }
            } elseif (!is_null($attribute)) {
                $this[$attribute] = $value;
            }
        }
    }

    /**
     * Append a child node to this element.
     *
     * @param Horde_Xml_Element $element The element to append.
     */
    public function appendChild(Horde_Xml_Element $element)
    {
        $element->setParent($this);
        $element->_ensureAppended();
    }

    /**
     * Get an XML string representation of this element
     *
     * Returns a string of this element's XML, including the XML
     * prologue.
     *
     * @return string
     */
    public function saveXml()
    {
        // Return a complete document including XML prologue.
        $doc = new DOMDocument($this->_element->ownerDocument->version,
                               $this->_element->ownerDocument->actualEncoding);
        $doc->appendChild($doc->importNode($this->_element, true));
        return $doc->saveXML();
    }

    /**
     * Get the XML for only this element
     *
     * Returns a string of this element's XML without prologue.
     *
     * @return string
     */
    public function saveXmlFragment()
    {
        return $this->_element->ownerDocument->saveXML($this->_element);
    }

    /**
     * Unserialization handler; parse $this->_element as either an XML
     * string or a real DOMElement.
     */
    public function __wakeup()
    {
        if ($this->_element instanceof DOMElement) {
            return true;
        }

        if ($this->_serialized) {
            $this->_element = $this->_serialized;
            $this->_serialized = null;
        }

        if (is_string($this->_element)) {
            $doc = new DOMDocument;
            if (!@$doc->loadXML($this->_element)) {
                throw new Horde_Xml_Element_Exception('DOMDocument cannot parse XML: ', error_get_last());
            }

            $this->_element = $doc->documentElement;
            return true;
        } elseif (!is_null($this->_element)) {
            throw new InvalidArgumentException('Horde_Xml_Element initialization value must be a DOMElement, a string, or null; '
                                               . (gettype($this->_element) == 'object' ? get_class($this->_element) : gettype($this->_element))
                                               . ' given');
        }
    }

    /**
     * Prepare for serialization
     *
     * @return array
     */
    public function __sleep()
    {
        $this->_serialized = $this->saveXml();
        return array('_serialized');
    }

    /**
     * Map variable access onto the underlying entry representation.
     *
     * Get-style access returns a Horde_Xml_Element representing the
     * child element accessed. To get string values, use method syntax
     * with the __call() overriding.
     *
     * @param string $var The property to access.
     * @return mixed
     */
    public function __get($var)
    {
        $nodes = $this->_children($var);
        $length = count($nodes);

        if ($length == 1) {
            return new Horde_Xml_Element($nodes[0]);
        } elseif ($length > 1) {
            return array_map(array($this, '_wrap_nodes'), $nodes);
        } else {
            // When creating anonymous nodes for __set chaining, don't
            // call appendChild() on them. Instead we pass the current
            // element to them as an extra reference; the child is
            // then responsible for appending itself when it is
            // actually set. This way "if ($foo->bar)" doesn't create
            // a phantom "bar" element in our tree.
            if (strpos($var, ':') !== false) {
                list($ns, $elt) = explode(':', $var, 2);
                $node = $this->_element->ownerDocument->createElementNS(Horde_Xml_Element::lookupNamespace($ns), $elt);
            } else {
                $node = $this->_element->ownerDocument->createElement($var);
            }
            $node = new Horde_Xml_Element($node);
            $node->setParent($this);
            return $node;
        }
    }

    /**
     * Helper function for array_map to wrap DOM nodes in
     * Horde_Xml_Element objects.
     */
    private function _wrap_nodes($e)
    {
        return new Horde_Xml_Element($e);
    }

    /**
     * Map variable sets onto the underlying entry representation.
     *
     * @param string $var The property to change.
     * @param string $val The property's new value.
     */
    public function __set($var, $val)
    {
        if (!is_scalar($val)) {
            throw new InvalidArgumentException('Element values must be scalars, ' . gettype($val) . ' given');
        }

        $this->_ensureAppended();

        $nodes = $this->_children($var);
        if (!$nodes) {
            if (strpos($var, ':') !== false) {
                list($ns, $elt) = explode(':', $var, 2);
                $node = $this->_element->ownerDocument->createElementNS(Horde_Xml_Element::lookupNamespace($ns), $var, $val);
                $this->_element->appendChild($node);
            } else {
                $node = $this->_element->ownerDocument->createElement($var, $val);
                $this->_element->appendChild($node);
            }
        } elseif (count($nodes) > 1) {
            throw new Horde_Xml_Element_Exception('Cannot set the value of multiple tags simultaneously.');
        } else {
            $nodes[0]->nodeValue = $val;
        }
    }

    /**
     * Map isset calls onto the underlying entry representation.
     *
     * Only supported by PHP 5.1 and later.
     */
    public function __isset($var)
    {
        // Look for access of the form {ns:var}. We don't use
        // _children() here because we can break out of the loop
        // immediately once we find something.
        if (strpos($var, ':') !== false) {
            list($ns, $elt) = explode(':', $var, 2);
            foreach ($this->_element->childNodes as $child) {
                if ($child->localName == $elt && $child->prefix == $ns) {
                    return true;
                }
            }
        } else {
            foreach ($this->_element->childNodes as $child) {
                if ($child->localName == $var) {
                    return true;
                }
            }
        }
    }

    /**
     * Get the value of an element with method syntax.
     *
     * Map method calls to get the string value of the requested
     * element. If there are multiple elements that match, this will
     * return an array of those objects.
     *
     * @param string $var The element to get the string value of.
     *
     * @return mixed The node's value, null, or an array of nodes.
     */
    public function __call($var, $unused)
    {
        $nodes = $this->_children($var);

        if (!$nodes) {
            return null;
        } elseif (count($nodes) > 1) {
            return $nodes;
        } else {
            return $nodes[0]->nodeValue;
        }
    }

    /**
     * Remove all children matching $var.
     *
     * Only supported by PHP 5.1 and later.
     */
    public function __unset($var)
    {
        $nodes = $this->_children($var);
        foreach ($nodes as $node) {
            $parent = $node->parentNode;
            $parent->removeChild($node);
        }
    }

    /**
     * Returns the nodeValue of this element when this object is used
     * in a string context.
     *
     * @internal
     */
    public function __toString()
    {
        return $this->_element->nodeValue;
    }

    /**
     * Set the parent element of this object to another
     * Horde_Xml_Element.
     *
     * @internal
     */
    public function setParent(Horde_Xml_Element $element)
    {
        $this->_parentElement = $element;
        $this->_appended = false;
    }

    /**
     * Appends this element to its parent if necessary.
     *
     * @internal
     */
    protected function _ensureAppended()
    {
        if (!$this->_appended) {
            $parentDom = $this->_parentElement->getDom();
            if (!$parentDom->ownerDocument->isSameNode($this->_element->ownerDocument)) {
                $this->_element = $parentDom->ownerDocument->importNode($this->_element, true);
            }

            $parentDom->appendChild($this->_element);
            $this->_appended = true;
            $this->_parentElement->_ensureAppended();
        }
    }

    /**
     * Finds children with tagnames matching $var
     *
     * Similar to SimpleXML's children() method.
     *
     * @param string Tagname to match, can be either namespace:tagName or just tagName.
     * @return array
     */
    protected function _children($var)
    {
        $found = array();

        // Look for access of the form {ns:var}.
        if (strpos($var, ':') !== false) {
            list($ns, $elt) = explode(':', $var, 2);
            foreach ($this->_element->childNodes as $child) {
                if ($child->localName == $elt && $child->prefix == $ns) {
                    $found[] = $child;
                }
            }
        } else {
            foreach ($this->_element->childNodes as $child) {
                if ($child->localName == $var) {
                    $found[] = $child;
                }
            }
        }

        return $found;
    }

    /**
     * Required by the ArrayAccess interface.
     *
     * @internal
     */
    public function offsetExists($offset)
    {
        if (strpos($offset, ':') !== false) {
            list($ns, $attr) = explode(':', $offset, 2);
            return $this->_element->hasAttributeNS(Horde_Xml_Element::lookupNamespace($ns), $attr);
        } else {
            return $this->_element->hasAttribute($offset);
        }
    }

    /**
     * Required by the ArrayAccess interface.
     *
     * @internal
     */
    public function offsetGet($offset)
    {
        if (strpos($offset, ':') !== false) {
            list($ns, $attr) = explode(':', $offset, 2);
            return $this->_element->getAttributeNS(Horde_Xml_Element::lookupNamespace($ns), $attr);
        } else {
            return $this->_element->getAttribute($offset);
        }
    }

    /**
     * Required by the ArrayAccess interface.
     *
     * @internal
     */
    public function offsetSet($offset, $value)
    {
        if (!is_scalar($value)) {
            throw new InvalidArgumentException('Element values must be scalars, ' . gettype($value) . ' given');
        }

        $this->_ensureAppended();

        if (strpos($offset, ':') !== false) {
            list($ns, $attr) = explode(':', $offset, 2);
            return $this->_element->setAttributeNS(Horde_Xml_Element::lookupNamespace($ns), $attr, $value);
        } else {
            return $this->_element->setAttribute($offset, $value);
        }
    }

    /**
     * Required by the ArrayAccess interface.
     *
     * @internal
     */
    public function offsetUnset($offset)
    {
        if (strpos($offset, ':') !== false) {
            list($ns, $attr) = explode(':', $offset, 2);
            return $this->_element->removeAttributeNS(Horde_Xml_Element::lookupNamespace($ns), $attr);
        } else {
            return $this->_element->removeAttribute($offset);
        }
    }

}

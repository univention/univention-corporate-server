<?php
/**
 * $Horde: framework/Feed/lib/Horde/Feed/Base.php,v 1.1.2.4 2009-01-06 15:23:04 jan Exp $
 *
 * Portions Copyright 2005-2007 Zend Technologies USA Inc. (http://www.zend.com)
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @category Horde
 * @package Horde_Feed
 */

/**
 * The Horde_Feed_Base class is an abstract class representing feeds.
 *
 * Horde_Feed_Base implements two core PHP 5 interfaces: ArrayAccess
 * and Iterator. In both cases the collection being treated as an
 * array is considered to be the entry collection, such that iterating
 * over the feed takes you through each of the feed's entries.
 *
 * @category Horde
 * @package Horde_Feed
 */
abstract class Horde_Feed_Base extends Horde_Xml_Element implements Iterator, Countable {

    /**
     * Current index on the collection of feed entries for the
     * Iterator implementation
     *
     * @var integer
     */
    protected $_entryIndex = 0;

    /**
     * Cache of feed entries
     *
     * @var array
     */
    protected $_entries;

    /**
     * Our root ("home") URI
     *
     * @var string
     */
    protected $_uri;

    /**
     * Feed constructor
     *
     * The Horde_Feed_Base constructor takes the URI of a feed or a
     * feed represented as a string and loads it as XML.
     *
     * @throws Horde_Feed_Exception If loading the feed failed.
     *
     * @param mixed $xml The feed as a string, a DOMElement, or null.
     * @param string $uri The full URI of the feed, or null if unknown.
     */
    public function __construct($xml = null, $uri = null)
    {
        $this->_uri = $uri;

        try {
            parent::__construct($xml);
        } catch (Horde_Xml_Element_Exception $e) {
            throw new Horde_Feed_Exception('Unable to load feed: ' . $e->getMessage());
        }
    }

    /**
     * Handle null or array values for $this->_element by initializing
     * with $this->_emptyXml, and importing the array with
     * Horde_Xml_Element::fromArray() if necessary.
     *
     * @see Horde_Xml_Element::__wakeup
     * @see Horde_Xml_Element::fromArray
     */
    public function __wakeup()
    {
        // If we've been passed an array, we'll store it for importing
        // after initializing with the default "empty" feed XML.
        $importArray = null;
        if (is_null($this->_element)) {
            $this->_element = $this->_emptyXml;
        } elseif (is_array($this->_element)) {
            $importArray = $this->_element;
            $this->_element = $this->_emptyXml;
        }

        parent::__wakeup();

        if (!is_null($importArray)) {
            $this->fromArray($importArray);
        }
    }

    /**
     * Get the number of entries in this feed object.
     *
     * @return integer Entry count.
     */
    public function count()
    {
        return count($this->_entries);
    }

    /**
     * Required by the Iterator interface.
     *
     * @internal
     */
    public function rewind()
    {
        $this->_entryIndex = 0;
    }

    /**
     * Required by the Iterator interface.
     *
     * @internal
     *
     * @return mixed The current row, or null if no rows.
     */
    public function current()
    {
        return new $this->_entryClassName(
            $this->_entries[$this->_entryIndex]);
    }

    /**
     * Required by the Iterator interface.
     *
     * @internal
     *
     * @return mixed The current row number (starts at 0), or null if no rows
     */
    public function key()
    {
        return $this->_entryIndex;
    }

    /**
     * Required by the Iterator interface.
     *
     * @internal
     *
     * @return mixed The next row, or null if no more rows.
     */
    public function next()
    {
        ++$this->_entryIndex;
    }

    /**
     * Required by the Iterator interface.
     *
     * @internal
     *
     * @return boolean Whether the iteration is valid
     */
    public function valid()
    {
        return (0 <= $this->_entryIndex && $this->_entryIndex < $this->count());
    }

}

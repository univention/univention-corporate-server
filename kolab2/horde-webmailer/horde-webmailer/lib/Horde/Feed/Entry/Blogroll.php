<?php
/**
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Feed
 */

/**
 * Concrete class for working with Blogroll elements.
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Feed
 */
class Horde_Feed_Entry_Blogroll extends Horde_Feed_Entry_Base
{
    /**
     * The XML string for an "empty" outline element.
     *
     * @var string
     */
    protected $_emptyXml = '<outline xmlUrl=""/>';

    /**
     * Name of the XML element for Atom entries. Subclasses can
     * override this to something other than "entry" if necessary.
     *
     * @var string
     */
    protected $_entryElementName = 'outline';

    /**
     * Get a Horde_Feed object for the feed described by this outline element.
     *
     * @return Horde_Feed_Base
     */
    public function getFeed()
    {
        if (!$this['xmlUrl']) {
            throw new Horde_Feed_Exception('No XML URL in <outline/> element');
        }
        return Horde_Feed::readUri($this['xmlUrl']);
    }

    /**
     * Add child elements and attributes to this element from a simple key =>
     * value hash. Because feed list outline elements only use attributes, this
     * overrides Horde_Xml_Element#fromArray to set attributes whether the
     * #Attribute syntax is used or not.
     *
     * @see Horde_Xml_Element#fromArray
     *
     * @param $array Hash to import into this element.
     */
    public function fromArray($array)
    {
        foreach ($array as $key => $value) {
            $attribute = $key;
            if (substr($attribute, 0, 1) == '#') {
                $attribute = substr($attribute, 1);
            }
            $this[$attribute] = $value;
        }
    }

    /**
     * Make accessing some individual elements of the feed easier.
     *
     * @param string $var The property to access.
     * @return mixed
     */
    public function __get($var)
    {
        return $this->offsetGet($var);
    }

    /**
     * Map variable sets onto the underlying entry representation.
     *
     * @param string $var The property to change.
     * @param string $val The property's new value.
     */
    public function __set($var, $val)
    {
        return $this->offsetSet($var, $val);
    }

}

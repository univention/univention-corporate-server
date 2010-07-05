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
 * Blogroll feed list class
 *
 * This is not a generic OPML implementation, but one focused on lists of feeds,
 * i.e. blogrolls. See http://en.wikipedia.org/wiki/OPML for more information on
 * OPML.
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Feed
 */
class Horde_Feed_Blogroll extends Horde_Feed_Base
{
    /**
     * The classname for individual feed elements.
     * @var string
     */
    protected $_entryClassName = 'Horde_Feed_Entry_Blogroll';

    /**
     * The element name for individual feed elements (Atom <entry> elements).
     * @var string
     */
    protected $_entryElementName = 'outline';

    /**
     * The default namespace for blogrolls.
     * @var string
     */
    protected $_defaultNamespace = '';

    /**
     * The XML string for an "empty" Blogroll.
     * @var string
     */
    protected $_emptyXml = '<?xml version="1.0" encoding="utf-8"?><opml version="1.1"></opml>';

    /**
     * Set up the $_entries alias.
     */
    public function __wakeup()
    {
        parent::__wakeup();

        // Cache the individual outline elements so they don't need to be
        // searched for on every operation.
        $this->_entries = array();
        foreach ($this->_element->getElementsByTagName($this->_entryElementName) as $child) {
            if ($child->attributes->getNamedItem('xmlUrl')) {
                $this->_entries[] = $child;
            }
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
        switch ($var) {
        case 'body':
        case 'outline':
            return $this;

        case 'title':
            return $this->head->title;

        default:
            return parent::__get($var);
        }
    }

}

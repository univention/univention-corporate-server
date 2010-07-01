<?php
/**
 * $Horde: framework/Feed/lib/Horde/Feed/Rss.php,v 1.1.2.5 2009-01-06 15:23:04 jan Exp $
 *
 * Portions Copyright 2005-2007 Zend Technologies USA Inc. (http://www.zend.com)
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @category Horde
 * @package  Horde_Feed
 */

/**
 * RSS channel class
 *
 * The Horde_Feed_Rss class is a concrete subclass of Horde_Feed_Base
 * meant for representing RSS channels. It does not add any methods to
 * its parent, just provides a classname to check against with the
 * instanceof operator, and expects to be handling RSS-formatted data
 * instead of Atom.
 *
 * @category Horde
 * @package  Horde_Feed
 */
class Horde_Feed_Rss extends Horde_Feed_Base
{
    /**
     * The classname for individual channel elements.
     *
     * @var string
     */
    protected $_entryClassName = 'Horde_Feed_Entry_Rss';

    /**
     * The element name for individual channel elements (RSS <item>s).
     *
     * @var string
     */
    protected $_entryElementName = 'item';

    /**
     * The default namespace for RSS channels.
     *
     * @var string
     */
    protected $_defaultNamespace = 'rss';

    /**
     * The XML string for an "empty" RSS feed.
     *
     * @var string
     */
    protected $_emptyXml = '<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel></channel></rss>';

    /**
     * Set up the $_entries alias.
     */
    public function __wakeup()
    {
        parent::__wakeup();

        // Cache the individual feed elements so they don't need to be
        // searched for on every operation.
        $this->_entries = array();
        foreach ($this->_element->childNodes as $child) {
            if ($child->localName == $this->_entryElementName) {
                $this->_entries[] = $child;
            }
        }

        // Brute-force search for $_entryElementName if we haven't
        // found any so far.
        if (!count($this->_entries)) {
            foreach ($this->_element->getElementsByTagName($this->_entryElementName) as $child) {
                $this->_entries[] = $child;
            }
        }
    }

    /**
     * Make accessing some individual elements of the channel easier.
     *
     * Special accessors 'item' and 'items' are provided so that if
     * you wish to iterate over an RSS channel's items, you can do so
     * using foreach ($channel->items as $item) or foreach
     * ($channel->item as $item).
     *
     * @param string $var The property to access.
     * @return mixed
     */
    public function __get($var)
    {
        switch ($var) {
        case 'item':
            // fall through to the next case
        case 'items':
            return $this;

        default:
            return parent::__get($var);
        }
    }

}

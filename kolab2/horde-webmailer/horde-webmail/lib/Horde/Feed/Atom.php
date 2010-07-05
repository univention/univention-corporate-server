<?php
/**
 * $Horde: framework/Feed/lib/Horde/Feed/Atom.php,v 1.1.2.5 2009-01-06 15:23:04 jan Exp $
 *
 * Portions Copyright 2005-2007 Zend Technologies USA Inc. (http://www.zend.com)
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @category Horde
 * @package  Horde_Feed
 */

/**
 * Atom feed class
 *
 * The Horde_Feed_Atom class is a concrete subclass of the general
 * Horde_Feed_Base class, tailored for representing an Atom feed. It shares all
 * of the same methods with its parent. The distinction is made in the format of
 * data that Horde_Feed_Atom expects, and as a further pointer for users as to
 * what kind of feed object they have been passed.
 *
 * @category Horde
 * @package  Horde_Feed
 */
class Horde_Feed_Atom extends Horde_Feed_Base
{
    /**
     * The classname for individual feed elements.
     *
     * @var string
     */
    protected $_entryClassName = 'Horde_Feed_Entry_Atom';

    /**
     * The element name for individual feed elements (Atom <entry>
     * elements).
     *
     * @var string
     */
    protected $_entryElementName = 'entry';

    /**
     * The default namespace for Atom feeds.
     *
     * @var string
     */
    protected $_defaultNamespace = 'atom';

    /**
     * The XML string for an "empty" Atom feed.
     *
     * @var string
     */
    protected $_emptyXml = '<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>';

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
    }

    /**
     * Easy access to <link> tags keyed by "rel" attributes.
     *
     * If $elt->link() is called with no arguments, we will attempt to return
     * the value of the <link> tag(s) like all other method-syntax attribute
     * access. If an argument is passed to link(), however, then we will return
     * the "href" value of the first <link> tag that has a "rel" attribute
     * matching $rel:
     *
     * $elt->link(): returns the value of the link tag.
     * $elt->link('self'): returns the href from the first <link rel="self"> in the entry.
     *
     * @param string $rel The "rel" attribute to look for.
     * @return mixed
     */
    public function link($rel = null)
    {
        if ($rel === null) {
            return parent::__call('link', null);
        }

        // Index link tags by their "rel" attribute.
        $links = parent::__get('link');
        if (!is_array($links)) {
            if ($links instanceof Horde_Xml_Element) {
                $links = array($links);
            } else {
                return $links;
            }
        }

        foreach ($links as $link) {
            if (empty($link['rel'])) {
                continue;
            }
            if ($rel == $link['rel']) {
                return $link['href'];
            }
        }

        return null;
    }

    /**
     * Make accessing some individual elements of the feed easier.
     *
     * Special accessors 'entry' and 'entries' are provided so that if you wish
     * to iterate over an Atom feed's entries, you can do so using foreach
     * ($feed->entries as $entry) or foreach ($feed->entry as $entry).
     *
     * @param string $var The property to access.
     * @return mixed
     */
    public function __get($var)
    {
        switch ($var) {
        case 'entry':
        case 'entries':
            return $this;

        default:
            return parent::__get($var);
        }
    }

}

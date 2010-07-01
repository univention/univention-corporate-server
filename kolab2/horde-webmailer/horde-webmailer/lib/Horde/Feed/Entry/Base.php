<?php
/**
 * $Horde: framework/Feed/lib/Horde/Feed/Entry/Base.php,v 1.1.2.4 2009-01-06 15:23:04 jan Exp $
 *
 * Portions Copyright 2005-2007 Zend Technologies USA Inc. (http://www.zend.com)
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @category Horde
 * @package Horde_Feed
 */

/**
 * Horde_Feed_Entry_Base represents a single entry in an Atom or RSS
 * feed.
 *
 * @category Horde
 * @package Horde_Feed
 */
abstract class Horde_Feed_Entry_Base extends Horde_Xml_Element {

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

}

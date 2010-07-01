<?php
/**
 * $Horde: framework/Feed/lib/Horde/Feed/Entry/Rss.php,v 1.1.2.5 2009-01-06 15:23:04 jan Exp $
 *
 * Portions Copyright 2005-2007 Zend Technologies USA Inc. (http://www.zend.com)
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @category Horde
 * @package  Horde_Feed
 */

/**
 * Concrete class for working with RSS items.
 *
 * @category Horde
 * @package  Horde_Feed
 */
class Horde_Feed_Entry_Rss extends Horde_Feed_Entry_Base
{
    /**
     * The XML string for an "empty" RSS entry.
     *
     * @var string
     */
    protected $_emptyXml = '<item/>';

}

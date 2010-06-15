<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command.php';

/**
 * $Horde: framework/SyncML/SyncML/Command/Sync/SyncElement.php,v 1.10 2004/05/26 17:46:15 chuck Exp $
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_SyncML
 */
class Horde_SyncML_Command_Sync_SyncElement extends Horde_SyncML_Command {

    var $_luid;
    var $_guid;
    var $_isSource;

    function &factory($command, $params = null)
    {
        @include_once 'Horde/SyncML/Command/Sync/' . $command . '.php';
        $class = 'Horde_SyncML_Command_Sync_' . $command;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            require_once 'PEAR.php';
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    function startElement($uri, $element, $attrs)
    {
        parent::startElement($uri, $element, $attrs);

        switch ($this->_xmlStack) {
        case 2:
            if ($element == 'Source') {
                $this->_isSource = true;
            }
            break;
        }
    }

    function endElement($uri, $element)
    {
        switch ($this->_xmlStack) {
        case 1:
            // Need to add sync elements to the Sync method?
            break;

        case 2:
            if ($element == 'Source') {
                $this->_isSource = false;
            } elseif ($element == 'Data') {
                $this->_content = trim($this->_chars);
            }
            break;

        case 3:
            if ($element == 'LocURI' && $this->_isSource) {
                $this->_luid = trim($this->_chars);
            }
            break;
        }

        parent::endElement($uri, $element);
    }

    function getLUID()
    {
        return $this->_luid;
    }

    function getGUID()
    {
        return $this->_guid;
    }

    function setLUID($luid)
    {
        $this->_luid = $luid;
    }

    function setGUID($guid)
    {
        $this->_guid = $guid;
    }

    function getContent()
    {
        return $this->_content;
    }

    function setContent($content)
    {
        $this->_content = $content;
    }

}

<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command/Sync/SyncElement.php';

/**
 * $Horde: framework/SyncML/SyncML/Command/Sync/ContentSyncElement.php,v 1.11 2004/05/26 17:43:29 chuck Exp $
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
class Horde_SyncML_Command_Sync_ContentSyncElement extends Horde_SyncML_Command_Sync_SyncElement {

    var $_content;

    function getContent()
    {
        return $this->_content;
    }

    function setContent($content)
    {
        $this->_content = $content;
    }

    function endElement($uri, $element)
    {
        switch ($this->_xmlStack) {
        case 2:
            if ($element == 'Data') {
                $this->_content = trim($this->_chars);
            }
            break;
        }

        parent::endElement($uri, $element);
    }

    function outputCommand($currentCmdID, $output, $command)
    {
        $state = $_SESSION['SyncML.state'];

        $attrs = array();
        $output->startElement($state->getURI(), $command, $attrs);

        $output->startElement($state->getURI(), 'CmdID', $attrs);
        $chars = $currentCmdID;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'CmdID');

        if (isset($this->_content)) {
            $output->startElement($state->getURI(), 'Data', $attrs);
            $chars = $this->_content;
            $output->characters($chars);
            $output->endElement($state->getURI(), 'Data');
        }

        $output->endElement($state->getURI(), $command);

        return $currentCmdID++;
    }

}

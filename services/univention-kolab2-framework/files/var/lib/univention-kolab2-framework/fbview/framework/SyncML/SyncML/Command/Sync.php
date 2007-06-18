<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command.php';
include_once 'Horde/SyncML/Command/Sync/SyncElement.php';

/**
 * $Horde: framework/SyncML/SyncML/Command/Sync.php,v 1.14 2004/05/26 17:46:15 chuck Exp $
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
class Horde_SyncML_Command_Sync extends Horde_Syncml_Command {

    var $_isInSource;
    var $_currentSyncElement;
    var $_syncElements = array();

    function output($currentCmdID, &$output)
    {
        $state = $_SESSION['SyncML.state'];

        $attrs = array();

        $output->startElement($state->getURI(), 'Sync', $attrs);

        $output->startElement($state->getURI(), 'CmdID', $attrs);
        $chars = $currentCmdID;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'CmdID');

        $output->startElement($state->getURI(), 'Target', $attrs);
        $output->startElement($state->getURI(), 'LocURI', $attrs);
        $chars = $this->_sourceURI;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'LocURI');
        $output->endElement($state->getURI(), 'Target');

        $output->startElement($state->getURI(), 'Source', $attrs);
        $output->startElement($state->getURI(), 'LocURI', $attrs);
        $chars = $this->_targetURI;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'LocURI');
        $output->endElement($state->getURI(), 'Source');

        $output->startElement($state->getURI(), 'NumberOfChanged', $attrs);
        // $chars = count($this->_syncElements);
        $chars = 0;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'NumberOfChanged');

        $output->endElement($state->getURI(), 'Sync');

        $currentCmdID++;

        // Not sure where the status commands need to fall, but this
        // is a start.
        Horde::logMessage('SyncML: $this->_targetURI = ' . $this->_targetURI, __FILE__, __LINE__,  PEAR_LOG_DEBUG);
        $sync = $state->getSync($this->_targetURI);

        $currentCmdID = $sync->startSync($currentCmdID, $output);

        foreach ($this->_syncElements as $element       ) {
            $currentCmdID = $sync->nextSyncCommand($currentCmdID, $element, $output);
        }

        $currentCmdID = $sync->endSync($currentCmdID, $output);

        $status = &new Horde_SyncML_Command_Status(RESPONSE_OK, 'Sync');
        $status->setState($state);
        $status->setCmdRef($this->_cmdID);

        if ($this->_targetURI != null) {
            $status->setTargetRef($this->_targetURI);
        }

        if ($this->_sourceURI != null) {
            $status->setSourceRef($this->_sourceURI);
        }

        return $status->output($currentCmdID, $output);
    }

    function getTargetURI()
    {
        return $this->_targetURI;
    }

    function startElement($uri, $element, $attrs)
    {
        parent::startElement($uri, $element, $attrs);

        switch ($this->_xmlStack) {
        case 2:
            if ($element == 'Replace' || $element == 'Add' || $element == 'Delete') {
                $this->_currentSyncElement = &Horde_SyncML_Command_Sync_SyncElement::factory($element);
                $this->_currentSyncElement->setVersion($this->_version);
                $this->_currentSyncElement->setCmdRef($this->_cmdID);
                $this->_currentSyncElement->setMsgID($this->_msgID);
            } elseif ($element == 'Target') {
                $this->_isInSource = false;
            } else {
                $this->_isInSource = true;
            }
            break;
        }

        if (isset($this->_currentSyncElement)) {
            $this->_currentSyncElement->startElement($uri, $element, $attrs);
        }
    }

    function endElement($uri, $element)
    {
        if (isset($this->_currentSyncElement)) {
            $this->_currentSyncElement->endElement($uri, $element);
        }

        switch ($this->_xmlStack) {
        case 2:
            if ($element == 'Replace' || $element == 'Add' || $element == 'Delete') {
                $this->_syncElements[] = $this->_currentSyncElement;
                unset($this->_currentSyncElement);
            }
            break;

        case 3:
            if ($element = 'LocURI') {
                if ($this->_isInSource) {
                    $this->_sourceURI = trim($this->_chars);
                } else {
                    $this->_targetURI = trim($this->_chars);
                }
            }
            break;
        }

        parent::endElement($uri, $element);
    }

    function characters($str)
    {
        if (isset($this->_currentSyncElement)) {
            $this->_currentSyncElement->characters($str);
        } else {
            if (isset($this->_chars)) {
                $this->_chars = $this->_chars . $str;
            } else {
                $this->_chars = $str;
            }
        }
    }

}

<?php

require_once 'SyncML/Command.php';

/**
 * The SyncML_Command_Status class provides a SyncML implementation of the
 * Status response as defined in SyncML Representation Protocol, version 1.1,
 * section 5.4.
 *
 * This is not strictly a command but specifies the request status code for a
 * corresponding SyncML command.
 *
 * $Horde: framework/SyncML/SyncML/Command/Status.php,v 1.15.10.13 2009-08-26 15:28:10 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Karsten Fourmont <fourmont@gmx.de>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package SyncML
 */
class SyncML_Command_Status extends SyncML_Command {

    /**
     * Name of the command.
     *
     * @var string
     */
    var $_cmdName = 'Status';

    /**
     * The command ID (CmdID) of the command sent to the client, that this
     * Status response refers to.
     *
     * @var integer
     */
    var $_CmdRef;

    /**
     * The message ID (Msg) of the message sent to the client, that this Status
     * response refers to.
     *
     * @var integer
     */
    var $_MsgRef;

    /**
     * The status response code, one of the RESPONSE_* constants.
     *
     * @var integer
     */
    var $_Status;

    /**
     * The command (Add, Replace, etc) sent to the client, that this Status
     * response refers to.
     *
     * @var string
     */
    var $_Cmd;

    /**
     * The client ID of the sent object, that this Status response refers to.
     *
     * This element is optional. If specified, Status response refers to a
     * single Item in the command sent to the client. It refers to all Items in
     * the sent command otherwise.
     *
     * @var string
     */
    var $_TargetRef;

    /**
     * The server ID of the sent object, that this Status response refers to.
     *
     * This element is optional. If specified, Status response refers to a
     * single Item in the command sent to the client. It refers to all Items in
     * the sent command otherwise.
     *
     * @var string
     */
    var $_SourceRef;

    /**
     * End element handler for the XML parser, delegated from
     * SyncML_ContentHandler::endElement().
     *
     * @param string $uri      The namespace URI of the element.
     * @param string $element  The element tag name.
     */
    function endElement($uri, $element)
    {
        switch (count($this->_stack)) {
        case 2:
            switch($element) {
            case 'CmdRef':
            case 'MsgRef':
            case 'Status':
                $this->{'_' . $element} = intval(trim($this->_chars));
                break;

            case 'Cmd':
            case 'TargetRef':
            case 'SourceRef':
                $this->{'_' . $element} = trim($this->_chars);
                break;
            }
            break;

        case 1:
            $state = &$_SESSION['SyncML.state'];
            switch ($this->_Cmd) {
            case 'Replace':
            case 'Add':
            case 'Delete':
                $changes = $state->serverChanges[$this->_MsgRef];
                /* Run through all stored changes and check if we find one
                 * that matches this Status' message and command IDs. */
                foreach ($changes as $db => $commands) {
                    foreach ($commands as $cmdId => $ids) {
                        if ($cmdId != $this->_CmdRef) {
                            continue;
                        }
                        foreach ($ids as $key => $id) {
                            /* If the Status has a SourceRef and/or TargetRef,
                             * it's a response to a single Item only. */
                            if ((isset($this->_SourceRef) &&
                                 $this->_SourceRef != $id[0]) ||
                                (isset($this->_TargetRef) &&
                                 $this->_TargetRef != $id[1])) {
                                continue;
                            }
                            /* Match found, remove from stored changes. */
                            unset($state->serverChanges[$this->_MsgRef][$db][$this->_CmdRef][$key]);
                            $sync = &$state->getSync($db);
                            /* This was a Replace originally, but the object
                             * wasn't found on the client. Try an Add
                             * instead. */
                            if ($this->_Cmd == 'Replace' &&
                                $this->_Status == RESPONSE_NOT_FOUND) {
                                $sync->setServerChange('add', $id[0], $id[1]);
                            }
                            if (isset($this->_SourceRef) || isset($this->_TargetRef)) {
                                break 3;
                            }
                        }
                    }
                }
                break;
            }
            break;
        }

        parent::endElement($uri, $element);
    }

}

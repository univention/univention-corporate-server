<?php

require_once 'SyncML/Command.php';

/**
 * The SyncML_Command_Alert class provides a SyncML implementation of the
 * Alert command as defined in SyncML Representation Protocol, version 1.1,
 * section 5.5.2.
 *
 * The Alert command is used for sending custom content information to the
 * recipient. The command provides a mechanism for communicating content
 * information, such as state information or notifications to an application
 * on the recipient device.
 *
 * $Horde: framework/SyncML/SyncML/Command/Alert.php,v 1.18.10.17 2009-04-07 11:13:05 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @author  Karsten Fourmont <karsten@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package SyncML
 */
class SyncML_Command_Alert extends SyncML_Command {

    /**
     * Name of the command.
     *
     * @var string
     */
    var $_cmdName = 'Alert';

    /**
     * The alert type. Should be one of the ALERT_* constants.
     *
     * @var integer
     */
    var $_alert;

    /**
     * Source database of the Alert command.
     *
     * @var string
     */
    var $_sourceLocURI;

    /**
     * Target database of the Alert command.
     *
     * @var string
     */
    var $_targetLocURI;

    /**
     * The current time this synchronization happens, from the <Meta><Next>
     * element.
     *
     * @var string
     */
    var $_metaAnchorNext;

    /**
     * The last time when synchronization happened, from the <Meta><Last>
     * element.
     *
     * @var integer
     */
    var $_metaAnchorLast;

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
            if ($element == 'Data') {
                $this->_alert = intval(trim($this->_chars));
            }
            break;

        case 4:
            if ($element == 'LocURI') {
                switch ($this->_stack[2]) {
                case 'Source':
                    $this->_sourceLocURI = trim($this->_chars);
                    break;
                case 'Target':
                    $this->_targetLocURI = trim($this->_chars);
                    break;
                }
            }
            break;

        case 5:
            switch ($element) {
            case 'Next':
                $this->_metaAnchorNext = trim($this->_chars);
                break;
            case 'Last':
                $this->_metaAnchorLast = trim($this->_chars);
                break;
            }
            break;
        }

        parent::endElement($uri, $element);
    }

    /**
     * Implements the actual business logic of the Alert command.
     */
    function handleCommand($debug = false)
    {
        $state = &$_SESSION['SyncML.state'];
        // Handle unauthenticated first.
        if (!$state->authenticated) {
            $this->_outputHandler->outputStatus($this->_cmdID, $this->_cmdName,
                                                RESPONSE_INVALID_CREDENTIALS);
            return;
        }

        // Handle NEXT_MESSAGE Alert by doing nothing, except OK status
        // response.  Exception for Funambol: here we produce the output only
        // after an explicit ALERT_NEXT_MESSAGE.
        if ($this->_alert == ALERT_NEXT_MESSAGE) {
            $this->_outputHandler->outputStatus($this->_cmdID, $this->_cmdName,
                                                RESPONSE_OK);
            // @TODO: create a getDevice()->sentyncDataLate() method instead
            // of this:
            if (is_a($state->getDevice(), 'SyncML_Device_sync4j')) {
                // Now send client changes to server. This will produce the
                // <Sync> response.
                $sync = &$state->getSync($this->_targetLocURI);
                if ($sync) {
                    $sync->createSyncOutput($this->_outputHandler);
                }
            }
            return;
        }

        $database = $this->_targetLocURI;
        if (!$GLOBALS['backend']->isValidDatabaseURI($database)) {
            $this->_outputHandler->outputStatus($this->_cmdID, $this->_cmdName,
                                                RESPONSE_NOT_FOUND);
            return;
        }

        $clientAnchorNext = $this->_metaAnchorNext;

        if (!$debug &&
            ($this->_alert == ALERT_TWO_WAY ||
             $this->_alert == ALERT_ONE_WAY_FROM_CLIENT ||
             $this->_alert == ALERT_ONE_WAY_FROM_SERVER)) {
            // Check if we have information about previous sync.
            $r = $GLOBALS['backend']->readSyncAnchors($this->_targetLocURI);
            if (is_array($r)) {
                // Info about previous successful sync sessions found.
                list($clientlast, $serverAnchorLast) = $r;
                $GLOBALS['backend']->logMessage(
                    'Previous sync found for database ' . $database
                    . '; client timestamp: ' . $clientlast,
                    __FILE__, __LINE__, PEAR_LOG_DEBUG);

                // Check if anchor sent from client matches our own stored
                // data.
                if ($clientlast == $this->_metaAnchorLast) {
                    // Last sync anchors matche, TwoWaySync will do.
                    $anchormatch = true;
                    $GLOBALS['backend']->logMessage(
                        'Anchor timestamps match, TwoWaySync possible. Syncing data since '
                        . date('Y-m-d H:i:s', $serverAnchorLast),
                        __FILE__, __LINE__, PEAR_LOG_DEBUG);
                } else {
                    // Server and client have different anchors, enforce
                    // SlowSync/RefreshSync
                    $GLOBALS['backend']->logMessage(
                        'Client requested sync with anchor timestamp '
                        . $this->_metaAnchorLast
                        . ' but server has recorded timestamp '
                        . $clientlast . '. Enforcing SlowSync',
                        __FILE__, __LINE__, PEAR_LOG_INFO);
                    $anchormatch = false;
                    $clientlast = 0;
                }
            } else {
                // No info about previous sync, use SlowSync or RefreshSync.
                $GLOBALS['backend']->logMessage(
                    'No info about previous syncs found for device ' .
                    $state->sourceURI . ' and database ' . $database,
                    __FILE__, __LINE__, PEAR_LOG_DEBUG);
                $clientlast = 0;
                $serverAnchorLast = 0;
                $anchormatch = false;
            }
        } else {
            // SlowSync requested, no anchor check required.
            $anchormatch = true;
        }

        // Determine sync type and status response code.
        switch ($this->_alert) {
        case ALERT_TWO_WAY:
            if ($anchormatch) {
                $synctype = ALERT_TWO_WAY;
                $response = RESPONSE_OK;
            } else {
                $synctype = ALERT_SLOW_SYNC;
                $response = RESPONSE_REFRESH_REQUIRED;
            }
            break;

        case ALERT_SLOW_SYNC:
            $synctype = ALERT_SLOW_SYNC;
            $response = $anchormatch ? RESPONSE_OK : RESPONSE_REFRESH_REQUIRED;
            break;

        case ALERT_ONE_WAY_FROM_CLIENT:
            if ($anchormatch) {
                $synctype = ALERT_ONE_WAY_FROM_CLIENT;
                $response = RESPONSE_OK;
            } else {
                $synctype = ALERT_REFRESH_FROM_CLIENT;
                $response = RESPONSE_REFRESH_REQUIRED;
            }
            break;

        case ALERT_REFRESH_FROM_CLIENT:
            $synctype = ALERT_REFRESH_FROM_CLIENT;
            $response = $anchormatch ? RESPONSE_OK : RESPONSE_REFRESH_REQUIRED;
            break;

        case ALERT_ONE_WAY_FROM_SERVER:
            if ($anchormatch) {
                $synctype = ALERT_ONE_WAY_FROM_SERVER;
                $response = RESPONSE_OK;
            } else {
                $synctype = ALERT_REFRESH_FROM_SERVER;
                $response = RESPONSE_REFRESH_REQUIRED;
            }
            break;

        case ALERT_REFRESH_FROM_SERVER:
            $synctype = ALERT_REFRESH_FROM_SERVER;
            $response = $anchormatch ? RESPONSE_OK : RESPONSE_REFRESH_REQUIRED;
            break;

        case ALERT_RESUME:
            // @TODO: Suspend and Resume is not supported yet
            $synctype = ALERT_SLOW_SYNC;
            $response = RESPONSE_REFRESH_REQUIRED;
            break;

        default:
            $GLOBALS['backend']->logMessage(
                'Unknown sync type ' . $this->_alert,
                __FILE__, __LINE__, PEAR_LOG_ERR);
            break;
        }

        // Now set interval to retrieve server changes from, defined by
        // ServerAnchor [Last,Next]
        if ($synctype != ALERT_TWO_WAY &&
            $synctype != ALERT_ONE_WAY_FROM_CLIENT &&
            $synctype != ALERT_ONE_WAY_FROM_SERVER) {
            $serverAnchorLast = 0;
            // Erase existing map:
            if (!$debug &&
                (($anchormatch &&
                  CONFIG_DELETE_MAP_ON_REQUESTED_SLOWSYNC) ||
                 (!$anchormatch &&
                  CONFIG_DELETE_MAP_ON_ANCHOR_MISMATCH_SLOWSYNC))) {
                $GLOBALS['backend']->eraseMap($this->_targetLocURI);
            }
        }
        $serverAnchorNext = $debug ? time() : $GLOBALS['backend']->getCurrentTimeStamp();

        // Now create the actual SyncML_Sync object, if it doesn't exist yet.
        $sync = &$state->getSync($this->_targetLocURI);
        if (!$sync) {
            $GLOBALS['backend']->logMessage(
                'Creating SyncML_Sync object for database '
                . $this->_targetLocURI .  '; sync type ' . $synctype,
                __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $sync = new SyncML_Sync($synctype,
                                    $this->_targetLocURI,
                                    $this->_sourceLocURI,
                                    $serverAnchorLast, $serverAnchorNext,
                                    $clientAnchorNext);
            $state->setSync($this->_targetLocURI, $sync);
        }

        $this->_outputHandler->outputStatus($this->_cmdID, $this->_cmdName,
                                            $response,
                                            $this->_targetLocURI,
                                            $this->_sourceLocURI,
                                            $this->_metaAnchorNext,
                                            $this->_metaAnchorLast);

        $this->_outputHandler->outputAlert($synctype,
                                           $sync->getClientLocURI(),
                                           $sync->getServerLocURI(),
                                           $sync->getServerAnchorLast(),
                                           $sync->getServerAnchorNext());
    }

}

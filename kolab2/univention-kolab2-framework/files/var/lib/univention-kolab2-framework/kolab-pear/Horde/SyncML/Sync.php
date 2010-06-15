<?php
/**
 * $Horde: framework/SyncML/SyncML/Sync.php,v 1.1 2004/05/26 17:32:49 chuck Exp $
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
class Horde_SyncML_Sync {

    /**
     * Target, either contacts, notes, events,
     */
    var $targetLocURI;

    var $sourceLocURI;

    /**
     * Return if all commands success.
     */
    var $globalSuccess;

    /**
     * This is the content type to use to export data.
     */
    var $preferedContentType;

    function &factory($alert)
    {
        switch ($alert) {
        case ALERT_TWO_WAY:
            include_once 'Horde/SyncML/Sync/TwoWaySync.php';
            return new Horde_SyncML_Sync_TwoWaySync();

        case ALERT_SLOW_SYNC:
            include_once 'Horde/SyncML/Sync/SlowSync.php';
            return new Horde_SyncML_Sync_SlowSync();

        case ALERT_ONE_WAY_FROM_CLIENT:
            include_once 'Horde/SyncML/Sync/OneWayFromClientSync.php';
            return new Horde_SyncML_Sync_OneWayFromClientSync();

        case ALERT_REFRESH_FROM_CLIENT:
            include_once 'Horde/SyncML/Sync/RefreshFromClientSync.php';
            return new Horde_SyncML_Sync_RefreshFromClientSync();

        case ALERT_ONE_WAY_FROM_SERVER:
            include_once 'Horde/SyncML/Sync/OneWayFromServerSync.php';
            return new Horde_SyncML_Sync_OneWayFromServerSync();

        case ALERT_REFRESH_FROM_SERVER:
            include_once 'Horde/SyncML/Sync/RefreshFromServerSync.php';
            return new Horde_SyncML_Sync_RefreshFromServerSync();
        }

        require_once 'PEAR.php';
        return PEAR::raiseError('Alert ' . $alert . ' not found.');
    }

    function nextSyncCommand($currentCmdID, &$syncCommand, &$output)
    {
        $syncComand->setSuccess($this->runCommand($syncCommand));

        return $syncCommand->output($currentCmdID, $output);
    }

    function startSync($currentCmdID, &$output)
    {
        return $currentCmdID;
    }

    function endSync($currentCmdID, &$output)
    {
        return $currentCmdID;
    }

    function runSyncCommand($command)
    {
        global $registry;

        $guid = false;
        if (is_a($command, 'Horde_SyncML_Command_Sync_Add')) {
            $guid = $registry->call($targetLocURI . '/import', array($command->getContent(), $command->getContentType()));
            if (!is_a($guid, 'PEAR_Error')) {
                $this->currentState->setUID($this->type, $command->getLocURI(), $guid);
            }
        } elseif (is_a($command, 'Horde_SyncML_Command_Sync_Delete')) {
            $guid = $this->currentState->removeUID($this->type, $command->getLocURI());
            if (!is_a($guid, 'PEAR_Error')) {
                $registry->call($targetLocURI . '/remove', array($guid));
            }
        } elseif (is_a($command, 'Horde_SyncML_Command_Sync_Replace')) {
            $guid = $this->currentState->getGlobalUID($this->type, $command->getLocURI());
            if ($guid) {
                $guid = call($targetLocURI . 'replace', array($guid, $command->getContent(), $command->getContentType()));
            } else {
                $guid = call($targetLocURI . '/import', $command->getContent(), $command->getContentType());
                $this->currentState->setUID($this->type, $command->getLocURI(), $guid);
            }
        }

        return $shareid;
    }

}

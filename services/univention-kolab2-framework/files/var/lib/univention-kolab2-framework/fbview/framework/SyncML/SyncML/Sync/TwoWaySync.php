<?php

include_once 'Horde/SyncML/Sync.php';

/**
 * $Horde: framework/SyncML/SyncML/Sync/TwoWaySync.php,v 1.8 2004/05/26 17:32:50 chuck Exp $
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
class Horde_SyncML_Sync_TwoWaySync extends Horde_SyncML_Sync {

    function endSync($currentCmdID, &$output)
    {
        global $registry;

        $state = $_SESSION['SyncML.state'];

        // Get changes.
        $changes = $registry->call($this->targetLocURI, '/listBy', array('timestamp' => 0, 'action' => 'modify'));
        foreach ($changes as $change) {
            $locid = $state->getLocID($changes);
            // Add a replace.
            $replace = &new Horde_SyncML_Command_Sync_ContentSyncElement();

            $replace->setContent($registry->call($this->targetLocURI . '/export',
                                                 array('guid' => $change, 'contentType' => $this->_currentState->getPreferedContentType($this->targetLocURI))));

            $currentCmdID = $replace->outputCommand($currentCmdID, $output, 'Replace');
        }

        // Get deletes.
        $deletes = $registry->call($this->targetLocURI, '/listByAction', array('timestamp' => 0, 'action' => 'delete'));
        foreach ($deletes as $delete) {
            $locid = $state->getLocID($delete);
            if ($locid) {
                // Add a replace.
                $delete = &new Horde_SyncML_Command_Sync_ContentSyncElement();

                $currentCmdID = $delete->outputCommand($currentCmdID, $output, 'Delete');
            }
        }

        // Get adds.
        $adds = $registry->call($this->targetLocURI, '/listByAction', array('timestamp' => 0, 'action' => 'add'));
        foreach ($adds as $add) {
            $locid = $state->getLocID($adds);
            // Add a replace.
            $add = &new Horde_SyncML_Command_Sync_ContentSyncElement();

            $replace->setContent($registry->call($this->targetLocURI . '/export',
                                                 array('guid' => $change, 'contentType' => $this->_currentState->getPreferedContentType($this->targetLocURI))));

            $currentCmdID = $add->outputCommand($currentCmdID, $output, 'Add');
        }

        return $currentCmdID;
    }

}

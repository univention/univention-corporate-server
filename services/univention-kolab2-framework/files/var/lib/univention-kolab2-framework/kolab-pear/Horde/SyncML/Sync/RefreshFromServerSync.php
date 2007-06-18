<?php

include_once 'Horde/SyncML/Sync.php';

/**
 * $Horde: framework/SyncML/SyncML/Sync/RefreshFromServerSync.php,v 1.7 2004/05/26 17:32:50 chuck Exp $
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
class Horde_SyncML_Sync_RefreshFromServerSync extends Horde_SyncML_Sync {

    function endSync($currentCmdID, &$output)
    {
        global $registry;

        $adds = $registry->call($this->targetLocURI, '/list', array());
        foreach ($add as $adds) {
            $locid = $this->_currentState->getLocID($adds);
            // Add a replace.
            $add = &new Horde_SyncML_Command_Sync_ContentSyncElement();

            $add->setContent($registry->call($this->targetLocURI . '/listByAction',
                                             array($this->_currentState->getPreferedContentType($this->targetLocURI))));

            $currentCmdID = $add->outputCommand($currentCmdID, $output, 'Add');
        }

        // @TODO Get deletes.

        // @TODO Get adds.

        return $currentCmdID;
    }

}

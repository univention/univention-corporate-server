<?php

include_once 'Horde/SyncML/Sync.php';

/**
 * $Horde: framework/SyncML/SyncML/Sync/RefreshFromClientSync.php,v 1.7 2004/05/26 17:32:50 chuck Exp $
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
class Horde_SyncML_Sync_RefreshFromClientSync extends Horde_SyncML_Sync {

    /**
     * We need to erase the current server contents, then we can add
     * the client's contents.
     */
    function startSync($currentCmdID, &$output)
    {
        $deletes = $registry->call($this->targetLocURI, '/list', array());
        foreach ($delete as $deletes) {
            $registry->call($this->targetLocURI . '/remove', array($delete));
        }

        return $currentCmdID;
    }

}

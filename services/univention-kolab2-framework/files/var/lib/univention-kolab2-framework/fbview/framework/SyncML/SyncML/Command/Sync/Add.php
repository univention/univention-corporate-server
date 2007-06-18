<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command/Sync/SyncElement.php';

/**
 * $Horde: framework/SyncML/SyncML/Command/Sync/Add.php,v 1.9 2004/05/26 17:43:29 chuck Exp $
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
class Horde_SyncML_Command_Sync_Add extends Horde_SyncML_Command_Sync_SyncElement {

    function output($currentCmdID, $output)
    {
        $status = &new Horde_SyncML_Command_Status(RESPONSE_ITEM_ADDED, 'Add');
        $status->setCmdRef($this->_cmdID);

        if (isset($this->_luid)) {
            $status->setSourceRef($this->_luid);
        }

        return $status->output($currentCmdID, $output);
    }

}

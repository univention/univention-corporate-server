<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command.php';

/**
 * $Horde: framework/SyncML/SyncML/Command/Put.php,v 1.11 2004/05/26 17:43:29 chuck Exp $
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
class Horde_SyncML_Command_Put extends Horde_SyncML_Command {

    function output($currentCmdID, &$output )
    {
        $state = $_SESSION['SyncML.state'];

        $status = &new Horde_SyncML_Command_Status((($state->isAuthorized()) ? RESPONSE_OK : RESPONSE_INVALID_CREDENTIALS), 'Put');
        $status->setCmdRef($this->_cmdID);

        $status->setSourceRef('./devinf11');

        return $status->output($currentCmdID, $output);
    }

}

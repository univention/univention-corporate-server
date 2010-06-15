<?php

include_once 'Horde/SyncML/Command.php';

/**
 * The Horde_SyncML_Command_Final class.
 *
 * $Horde: framework/SyncML/SyncML/Command/Final.php,v 1.10 2004/05/26 17:41:30 chuck Exp $
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
class Horde_SyncML_Command_Final extends Horde_SyncML_Command {

    function output($currentCmdID, &$output)
    {
        $state = $_SESSION['SyncML.state'];

        $attrs = array();
        $output->startElement($state->getURI(), 'Final', $attrs);

        $output->endElement($state->getURI(), 'Final');

        return $currentCmdID;
    }

}

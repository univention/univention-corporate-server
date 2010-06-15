<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command.php';

/**
 * $Horde: framework/SyncML/SyncML/Command/Results.php,v 1.10 2004/05/26 17:41:30 chuck Exp $
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
class Horde_SyncML_Command_Results extends Horde_SyncML_Command {

    var $_cmdRef;

    function output($currentCmdID, &$output)
    {
        $state = $_SESSION['SyncML.state'];

        $attrs = array();
        $output->startElement($state->getURI(), 'Results', $attrs);

        $output->startElement($state->getURI(), 'CmdID', $attrs);
        $chars = $currentCmdID;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'CmdID');

        $output->startElement($state->getURI(), 'MsgRef', $attrs);
        $chars = $state->getMsgID();
        $output->characters($chars);
        $output->endElement($state->getURI(), 'MsgRef');

        $output->startElement($state->getURI(), 'CmdRef', $attrs);
        $chars = $this->_cmdRef;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'CmdRef');

        /*
        $output->startElement($state->getURI(), 'Meta', $attrs);
        $output->startElement($state->getURIMeta(), 'Type', $attrs);
        $chars = $this->_cmdRef;
        $output->characters($chars);
        $output->endElement($state->getURIMeta(), 'Type');
        $output->endElement($state->getURI(), 'Meta');

        $output->startElement($state->getURI(), 'Item', $attrs);
        $output->startElement($state->getURI(), 'Source', $attrs);
        $output->startElement($state->getURI(), 'LocURI', $attrs);
        $chars = $this->_locSourceURI;
        $output->characters($chars);
        $output->endElement($state->getURI(), 'LocURI');
        $output->endElement($state->getURI(), 'Source');

        $output->startElement($state->getURI(), 'Data', $attrs);

        // Need to send this information as opaque data so the WBXML
        // will understand it.
        $output->opaque($this->_data);

        // $chars = $this->_data;
        // $output->characters($chars);
        $output->endElement($state->getURI(), 'Data');
        $output->endElement($state->getURI(), 'Item');
        */

        $output->endElement($state->getURI(), 'Results');

        $currentCmdID++;

        return $currentCmdID;
    }

    /**
     * Setter for property cmdRef.
     *
     * @param string $cmdRef  New value of property cmdRef.
     */
    function setCmdRef($cmdRef)
    {
        $this->_cmdRef = $cmdRef;
    }

}

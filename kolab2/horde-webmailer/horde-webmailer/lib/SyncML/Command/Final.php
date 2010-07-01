<?php

require_once 'SyncML/Command.php';

/**
 * The SyncML_Command_Final class provides a SyncML implementation of the
 * Final command as defined in SyncML Representation Protocol, version 1.1,
 * section 5.1.7.
 *
 * The Final command is an indicator that the SyncML message is the last
 * message in the current SyncML package.
 *
 * $Horde: framework/SyncML/SyncML/Command/Final.php,v 1.10.10.11 2009-04-05 20:24:43 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package SyncML
 */
class SyncML_Command_Final extends SyncML_Command {

    /**
     * Name of the command.
     *
     * @var string
     */
    var $_cmdName = 'Final';

    /**
     * Implements the actual business logic of the Alert command.
     */
    function handleCommand($debug = false)
    {
        $state = &$_SESSION['SyncML.state'];

        // If the client hasn't sent us device info, request it now.
        // @todo: only do this once, not in every msg if the client does not
        // implement DevInf.
        $di = $state->deviceInfo;
        if (empty($di->Man)) {
            $this->_outputHandler->outputGetDevInf();
        }

        $GLOBALS['backend']->logMessage('Received <Final> from client.',
                                        __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $state->handleFinal($this->_outputHandler, $debug);
    }

}

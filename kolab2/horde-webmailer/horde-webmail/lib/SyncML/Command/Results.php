<?php

require_once 'SyncML/Command/Put.php';

/**
 * The SyncML_Command_Results class provides a SyncML implementation of the
 * Results command as defined in SyncML Representation Protocol, version 1.1,
 * section 5.5.12.
 *
 * The Results command is used to return the results of a Search or Get
 * command. Currently SyncML_Command_Results behaves the same as
 * SyncML_Command_Put. The only results we get is the same DevInf as for the
 * Put command.
 *
 * $Horde: framework/SyncML/SyncML/Command/Results.php,v 1.11.10.11 2009-01-06 15:23:38 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Nathan P Sharp
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package SyncML
 */
class SyncML_Command_Results extends SyncML_Command_Put {

    /**
     * Name of the command.
     *
     * @var string
     */
    var $_cmdName = 'Results';

}

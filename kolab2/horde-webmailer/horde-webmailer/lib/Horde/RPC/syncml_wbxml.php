<?php

require_once dirname(__FILE__) . '/syncml.php';

/**
 * The Horde_RPC_syncml_wbxml class provides a SyncML implementation of the
 * Horde RPC system using WBXML encoding.
 *
 * $Horde: framework/RPC/RPC/syncml_wbxml.php,v 1.11.10.11 2009-01-06 15:23:32 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Anthony Mills <amills@pyramid6.com>
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC_syncml_wbxml extends Horde_RPC_syncml {

    /**
     * Returns the Content-Type of the response.
     *
     * @return string  The MIME Content-Type of the RPC response.
     */
    function getResponseContentType()
    {
        return 'application/vnd.syncml+wbxml';
    }

}

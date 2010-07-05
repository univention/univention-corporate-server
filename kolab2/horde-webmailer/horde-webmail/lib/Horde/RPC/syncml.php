<?php

require_once 'SyncML.php';
require_once 'SyncML/Backend.php';

/**
 * The Horde_RPC_syncml class provides a SyncML implementation of the Horde
 * RPC system.
 *
 * $Horde: framework/RPC/RPC/syncml.php,v 1.18.10.15 2009-01-06 15:23:32 jan Exp $
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

class Horde_RPC_syncml extends Horde_RPC {

    /**
     * SyncML handles authentication internally, so bypass the RPC framework
     * auth check by just returning true here.
     */
    function authorize()
    {
        return true;
    }

    /**
     * Sends an RPC request to the server and returns the result.
     *
     * @param string $request  The raw request string.
     *
     * @return string  The XML encoded response from the server.
     */
    function getResponse($request)
    {
        $backendparms = array(
            /* Write debug output to this dir, must be writeable be web
             * server. */
            'debug_dir' => '/tmp/sync',
            /* Log all (wb)xml packets received or sent to debug_dir. */
            'debug_files' => true,
            /* Log everything. */
            'log_level' => PEAR_LOG_DEBUG);

        /* Create the backend. */
        $GLOBALS['backend'] = SyncML_Backend::factory('Horde', $backendparms);

        /* Handle request. */
        $h = new SyncML_ContentHandler();
        $response = $h->process(
            $request, $this->getResponseContentType(),
            Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/rpc.php',
                       true, -1));

        /* Close the backend. */
        $GLOBALS['backend']->close();

        return $response;
    }

    /**
     * Returns the Content-Type of the response.
     *
     * @return string  The MIME Content-Type of the RPC response.
     */
    function getResponseContentType()
    {
        return 'application/vnd.syncml+xml';
    }

}

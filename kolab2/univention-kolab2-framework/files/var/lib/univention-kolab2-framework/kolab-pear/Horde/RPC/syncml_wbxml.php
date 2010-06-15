<?php

include_once 'Horde/RPC/syncml.php';
include_once 'XML/WBXML/Decoder.php';
include_once 'XML/WBXML/Encoder.php';

/**
 * The Horde_RPC_syncml class provides a SyncML implementation of the Horde
 * RPC system.
 *
 * $Horde: framework/RPC/RPC/syncml_wbxml.php,v 1.9 2004/04/07 17:43:42 chuck Exp $
 *
 * Copyright 2003-2004 Chuck Hagenbuch <chuck@horde.org>, Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Anthony Mills <amills@pyramid6.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_RPC
 */

class Horde_RPC_syncml_wbxml extends Horde_RPC_syncml {

    /**
     * Sends an RPC request to the server and returns the result.
     *
     * @param string $request  The raw request string.
     *
     * @return string   The WBXML encoded response from the server (binary).
     */
    function getResponse($request)
    {
        // Very useful for debugging. Logs the wbxml packets to $this->_debugDir
        if (isset($this->_debugDir)) {
            $packetNum = @intval(file_get_contents($this->_debugDir . '/syncml_wbxml.packetnum'));
            if (!isset($packetNum)) {
                $packetNum = 0;
            }

            $fp = fopen($this->_debugDir . '/syncml_client_' . $packetNum . '.wbxml', 'wb');
            fwrite($fp, $request);
            fclose($fp);
        }

        $decoder = &new XML_WBXML_Decoder();
        $xmlinput = $decoder->decode($request);
        if (is_a($xmlinput, 'PEAR_Error')) {
            return '';
        }

        $xmloutput = parent::getResponse($xmlinput);

        $encoder = &new XML_WBXML_Encoder();
        $encoder->setVersion($decoder->getVersion());
        $encoder->setCharset($decoder->getCharsetStr());
        $wbxmloutput = $encoder->encode($xmloutput);

        if (isset($this->_debugDir)) {
            $fp = fopen($this->_debugDir . '/syncml_server_' . $packetNum . '.wbxml', 'wb');
            fwrite($fp, $wbxmloutput);
            fclose($fp);

            $packetNum++;
            $f = fopen($this->_debugDir . '/syncml_wbxml.packetnum', 'wb');
            fwrite($f, $packetNum);
            fclose($f);
        }

        return $wbxmloutput;
    }

    /**
     * Get the Content-Type of the response.
     *
     * @return string  The MIME Content-Type of the RPC response.
     */
    function getResponseContentType()
    {
        return 'application/vnd.syncml+wbxml';
    }

}

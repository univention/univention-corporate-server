<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/echo.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/**
 * Echos a mail for debugging.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/echo.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * Copyright 2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class Horde_Kolab_Filter_Transport_echo extends Horde_Kolab_Filter_Transport 
{
    /**
     * Create the transport handler.
     *
     * @return StdOutWrapper Wraps STDOUT as transport
     */
    function &_createTransport()
    {
        $transport = &new EchoWrapper();
        return $transport;
    }
}

/**
 * Defines an echo wrapper that provides functionality comparable to 
 * the Net/*MTP.php classes.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/echo.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * Copyright 2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class EchoWrapper
{
    /**
     * Pretends to connect to STDOUT.
     *
     * @return boolean Always true.
     */
    function connect()
    {
        return true;
    }

    /**
     * Pretends to disconnect from STDOUT.
     *
     * @return boolean Always true.
     */
    function disconnect()
    {
        return true;
    }

    /**
     * Set the sender.
     *
     * @return mixed Result from writing the sender to STDOUT.
     */
    function mailFrom($sender)
    {
        echo sprintf("Mail from sender: %s\r\n", $sender);
        return true;
    }

    /**
     * Set the recipient.
     *
     * @return mixed Result from writing the recipient to STDOUT.
     */
    function rcptTo($recipient)
    {
        echo sprintf("Mail to recipient: %s\r\n", $recipient);
        return true;
    }

    /**
     * Pretends to send commands to STDOUT.
     *
     * @param string $cmd The command.
     *
     * @return boolean Always true.
     */
    function _put($cmd)
    {
        return true;
    }

    /**
     * Pretends to handle STDOUT responses.
     *
     * @param string $code The response to parse.
     *
     * @return boolean Always true.
     */
    function _parseResponse($code)
    {
        return true;
    }

    /**
     * Echo data.
     *
     * @param string $data The data to write.
     *
     * @return mixed Result from writing data to STDOUT.
     */
    function _send($data)
    {
        echo $data;
        return true;
    }
}

<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/drop.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/**
 * Drops a mail instead of delivering it.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/drop.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * Copyright 2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class Horde_Kolab_Filter_Transport_drop extends Horde_Kolab_Filter_Transport 
{
    /**
     * Create the transport handler.
     *
     * @return DropWrapper Provides a null class as transport.
     */
    function &_createTransport()
    {
        $transport = &new DropWrapper();
        return $transport;
    }
}

/**
 * Defines a wrapper that provides functionality comparable to the
 * Net/*MTP.php classes.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/drop.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * Copyright 2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class DropWrapper
{
    /**
     * Pretends to connect.
     *
     * @return boolean Always true.
     */
    function connect()
    {
        return true;
    }

    /**
     * Pretends to disconnect.
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
     * @return boolean Always true.
     */
    function mailFrom($sender)
    {
        return true;
    }

    /**
     * Set the recipient.
     *
     * @return boolean Always true.
     */
    function rcptTo($recipient)
    {
        return true;
    }

    /**
     * Pretends to send commands.
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
     * Pretends to handle responses.
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
     * Write data.
     *
     * @param string $data The data to write.
     *
     * @return boolean Always true.
     */
    function _send($data)
    {
        return true;
    }
}

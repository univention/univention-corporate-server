<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/smtp.php,v 1.3.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/**
 * Provides SMTP for delivering mail.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/smtp.php,v 1.3.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class Horde_Kolab_Filter_Transport_smtp extends Horde_Kolab_Filter_Transport 
{
    /**
     * Create the transport handler.
     *
     * @return Net_SMTP The SMTP handler.
     */
    function &_createTransport() 
    {
        require_once 'Net/SMTP.php';

        if (!isset($this->_params['host'])) {
            $this->_params['host'] = '127.0.0.1';
        }

        if (!isset($this->_params['port'])) {
            $this->_params['port'] = 25;
        }

        $transport = &new Net_SMTP($this->_params['host'],
                                   $this->_params['port']);
        return $transport;
    }
}

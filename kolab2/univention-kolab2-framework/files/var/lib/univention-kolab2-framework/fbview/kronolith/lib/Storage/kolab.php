<?php

require_once 'Horde/iCalendar.php';

/**
 * Horde Kronolith free/busy driver for the Kolab IMAP Server.
 * Copyright (C) 2003 Code Fusion, cc.
 *
 * $Horde: kronolith/lib/Storage/kolab.php,v 1.3 2004/05/24 12:42:54 stuart Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Bingë <s.binge@codefusion.co.za>
 * @version $Revision: 1.1.2.1 $
 * @package Kronolith
 */
class Kronolith_Storage_kolab extends Kronolith_Storage {

    var $_params = array();

    function Kronolith_Storage_kolab($user, $params = array())
    {
        $this->_user = $user;

        $this->_params = $params;

        $this->_params['folder'] = array_key_exists('folder', $params)
            ? $params['folder'] : '/freebusy';
        $this->_params['server'] = array_key_exists('server', $params)
            ? $params['server'] : $GLOBALS["conf"]["kolab"]["server"];
    }

    function search($email, $private_only = false)
    {
        $vfb = Kolab::retrieveFreeBusy($this->_params['server'], $this->_params['folder'], $email);
        if (is_a($vfb, 'PEAR_Error')) {
            if ($vfb->code == 404) {
                return PEAR::raiseError(_("Not found"), KRONOLITH_ERROR_FB_NOT_FOUND);
            }
            return $vfb;
        }

        $iCal = new Horde_iCalendar;
        $iCal->parsevCalendar($vfb);
        $fb = &$iCal->findComponent('VFREEBUSY');
        if ($fb === false) {
            return PEAR::raiseError(_("Not found"), KRONOLITH_ERROR_FB_NOT_FOUND);
        }

        return $fb;
    }

    function store($email, $vfb, $public = false)
    {
        $iCal = new Horde_iCalendar;
        $iCal->addComponent($vfb);
        $vfbfile = $iCal->exportvCalendar();

        return Kolab::storeFreeBusy($this->_params['server'], $this->_params['folder'], $vfbfile);
    }

}

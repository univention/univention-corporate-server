<?php

require_once 'Horde/iCalendar.php';
require_once 'Horde/Kolab.php';

/**
 * Horde Kronolith free/busy driver for the Kolab IMAP Server.
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * $Horde: kronolith/lib/Storage/kolab.php,v 1.4.10.11 2009-01-06 15:24:47 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * not receive such a file, see also http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Kronolith
 */
class Kronolith_Storage_kolab extends Kronolith_Storage {

    var $_params = array();

    function Kronolith_Storage_kolab($user, $params = array())
    {
        $this->_user = $user;
        $this->_params = $params;
    }

    function search($email, $private_only = false)
    {
        global $conf;

        @include_once 'Horde/Kolab/Session.php';

        if (class_exists('Horde_Kolab_Session')) {
            $session = &Horde_Kolab_Session::singleton();
            $server = $session->freebusy_server;
        } else if (!is_callable('Kolab', 'getServer')) {
            $server = sprintf('%s://%s:%d/freebusy/',
                              $conf['storage']['freebusy']['protocol'],
                              $conf['kolab']['imap']['server'],
                              $conf['storage']['freebusy']['port']);
        } else {
            $server = sprintf('%s://%s:%d/freebusy/',
                              $conf['storage']['freebusy']['protocol'],
                              Kolab::getServer('imap'),
                              $conf['storage']['freebusy']['port']);
        }

        $fb_url = sprintf('%s/%s.xfb', $server, $email);

        $options['method'] = 'GET';
        $options['timeout'] = 5;
        $options['allowRedirects'] = true;

        if (!empty($GLOBALS['conf']['http']['proxy']['proxy_host'])) {
            $options = array_merge($options, $GLOBALS['conf']['http']['proxy']);
        }

        require_once 'HTTP/Request.php';
        $http = new HTTP_Request($fb_url, $options);
        $http->setBasicAuth(Auth::getAuth(), Auth::getCredential('password'));
        @$http->sendRequest();
        if ($http->getResponseCode() != 200) {
            return PEAR::raiseError(sprintf(_("Unable to retrieve free/busy information for %s"),
                                            $email), KRONOLITH_ERROR_FB_NOT_FOUND);
        }
        $vfb_text = $http->getResponseBody();

        $iCal = new Horde_iCalendar;
        $iCal->parsevCalendar($vfb_text);

        $vfb = &$iCal->findComponent('VFREEBUSY');
        if ($vfb === false) {
            return PEAR::raiseError(sprintf(_("No free/busy information is available for %s"),
                                    $email), KRONOLITH_ERROR_FB_NOT_FOUND);
        }

        return $vfb;
    }

    function store($email, $vfb, $public = false)
    {
        // We don't care about storing FB info at the moment; we rather let
        // Kolab's freebusy.php script auto-generate it for us.
        return true;
    }

}

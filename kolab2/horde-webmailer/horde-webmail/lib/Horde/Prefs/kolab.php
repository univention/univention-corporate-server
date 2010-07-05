<?php

require_once 'Horde/Prefs/ldap.php';
require_once 'Horde/Kolab.php';

/**
 * Kolab implementation of the Horde preference system. Derives from the
 * Prefs_ldap LDAP authentication object, and simply provides parameters to it
 * based on the global Kolab configuration.
 *
 * $Horde: framework/Prefs/Prefs/kolab.php,v 1.1.10.12 2008-02-29 10:21:25 wrobel Exp $
 *
 * Copyright 2004-2007 Stuart Binge <s.binge@codefusion.co.za>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Binge <s.binge@codefusion.co.za>
 * @since   Horde 1.3
 * @package Horde_Prefs
 */
class Prefs_kolab extends Prefs_ldap {

    /**
     * Constructs a new Kolab preferences object.
     *
     * @param string $user      The user who owns these preferences.
     * @param string $password  The password associated with $user.
     * @param string $scope     The current application scope.
     * @param array $params     A hash containing connection parameters.
     * @param boolean $caching  Should caching be used?
     */
    function Prefs_kolab($user, $password, $scope = '',
                         $params = array(), $caching = false)
    {
        $params = array('hostspec' => Kolab::getServer('ldap'),
                        'port' => $GLOBALS['conf']['kolab']['ldap']['port'],
                        'version' => '3',
                        'basedn' => $GLOBALS['conf']['kolab']['ldap']['basedn'],
                        'writedn' => 'user',
                        'searchdn' => $GLOBALS['conf']['kolab']['ldap']['phpdn'],
                        'searchpw' => $GLOBALS['conf']['kolab']['ldap']['phppw'],
                        'uid' => 'mail');

        parent::Prefs_ldap($user, $password, $scope, $params, $caching);
    }

}

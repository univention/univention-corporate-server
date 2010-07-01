<?php

if (!function_exists('_prefs_hook_from_addr')) {
    function _prefs_hook_from_addr()
    {
        require_once 'Horde/Kolab/Session.php';
        $session = Horde_Kolab_Session::singleton();
        if (!is_a($session, 'PEAR_Error')) {
            return $session->user_mail;
        }
        return '';
    }
}

if (!function_exists('_prefs_hook_fullname')) {
    function _prefs_hook_fullname()
    {
        require_once 'Horde/Kolab/Session.php';
        $session = Horde_Kolab_Session::singleton();
        if (!is_a($session, 'PEAR_Error')) {
            return $session->user_name;
        }
        return '';
    }
}

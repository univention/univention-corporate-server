<?php
/**
 * Class for handling a list of credentials stored in a user's preferences.
 *
 * $Horde: framework/Prefs/Prefs/Credentials.php,v 1.2.2.3 2009-01-06 15:23:31 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.2.1
 * @package Horde_Prefs
 */
class Prefs_Credentials {

    /**
     * The Horde application currently processed.
     *
     * @see singleton()
     * @var string
     */
    var $app;

    /**
     * A list of preference field names and their values.
     *
     * @var array
     */
    var $_credentials = array();

    /**
     * Constructor.
     */
    function Prefs_Credentials()
    {
        $credentials = @unserialize($GLOBALS['prefs']->getValue('credentials'));
        if (!$credentials) {
            return;
        }
        foreach ($credentials as $app => $app_prefs) {
            foreach ($app_prefs as $name => $value) {
                $this->_credentials['credentials[' . $app . '][' . $name . ']'] = $value;
            }
        }
    }

    /**
     * Returns a single instance of the Prefs_Credentials class, and sets the
     * curently processed application.
     *
     * @param string $app  The current application.
     *
     * @return Prefs_Credentials  A Prefs_Credentials instance.
     */
    function singleton($app)
    {
        static $instance;
        if (!isset($instance)) {
            $instance = new Prefs_Credentials();
        }
        $instance->app = $app;
        return $instance;
    }

    /**
     * Returns a list of available credentials collected from all Horde
     * applications.
     *
     * @return array  A list of Horde applications and their credentials.
     */
    function getCredentials()
    {
        static $credentials_prefs;
        if (isset($credentials_prefs)) {
            return $credentials_prefs;
        }

        $credentials_prefs = array();
        foreach ($GLOBALS['registry']->listApps() as $app) {
            $credentials = $GLOBALS['registry']->callByPackage($app, 'authCredentials');
            if (is_a($credentials, 'PEAR_Error') || !count($credentials)) {
                continue;
            }
            $credentials_prefs[$app] = array();
            foreach ($credentials as $name => $credential) {
                $pref = 'credentials[' . $app . '][' . $name . ']';
                $credential['shared'] = true;
                $credentials_prefs[$app][$pref] = $credential;
            }
            continue;
        }

        return $credentials_prefs;
    }

    /**
     * Displays the preference interface for setting all available
     * credentials.
     */
    function showUI()
    {
        global $registry;

        $credentials = Prefs_Credentials::getCredentials();
        $vspace = '';
        foreach ($credentials as $app => $_prefs) {
            $prefs = Prefs_Credentials::singleton($app);
            echo $vspace . '<h2 class="smallheader">';
            printf(_("%s authentication credentials"),
                   $GLOBALS['registry']->get('name', $app));
            echo '</h2>';
            foreach (array_keys($_prefs) as $pref) {
                if (!empty($_prefs[$pref]['help'])) {
                    require_once 'Horde/Help.php';
                    $helplink = Help::link(!empty($_prefs[$pref]['shared']) ? 'horde' : $registry->getApp(), $_prefs[$pref]['help']);
                } else {
                    $helplink = null;
                }
                require $GLOBALS['registry']->get('templates') . '/prefs/' . $_prefs[$pref]['type'] . '.inc';
            }
            $vspace = '<br />';
        }
    }

    /**
     * Returns the value of a credential for the currently processed
     * application.
     *
     * @see Prefs::getValue()
     *
     * @param string $pref  A credential name.
     *
     * @return mixed  The credential's value, either from the user's
     *                preferences, or from the default value, or null.
     */
    function getValue($pref)
    {
        if (isset($this->_credentials[$pref])) {
            return $this->_credentials[$pref];
        }
        $credentials = Prefs_Credentials::getCredentials();
        if (isset($credentials[$this->app][$pref]['value'])) {
            return $credentials[$this->app][$pref]['value'];
        }
        return null;
    }

}

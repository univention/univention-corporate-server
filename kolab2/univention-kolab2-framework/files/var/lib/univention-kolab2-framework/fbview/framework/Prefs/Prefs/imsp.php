<?php
/**
 * Prefrence storage implementation for an IMSP server.
 *
 * $Horde: framework/Prefs/Prefs/imsp.php,v 1.1 2004/04/16 22:55:32 chuck Exp $
 *
 * Copyright 2004 Michael Rubinsky <mike@theupstairsroom.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @version $Revision: 1.1.2.1 $
 * @author  Michael Rubinsky <mike@theupstairsroom.com>
 * @package Horde_Prefs
 */
class Prefs_imsp extends Prefs {

    /**
     * Constructor function.
     * $params must contain:
     * 'auth_method', 'server', 'port'
     *
     * @param string $user Username of current user.
     * @param string $password Password for current user.
     * @param string $scope The scope for these preferences.
     * @param array $params The parameters needed for this object.
     * @param boolean $caching are we using session cache?
     */
    function Prefs_imsp($user, $password = '', $scope = '',
                        $params = null, $caching = true)
    {
        global $conf;

        parent::Prefs();
        require_once 'Net/IMSP.php';

        $this->_scope = $scope;
        $this->_caching = $caching;
        $this->_user = $user;
        $this->params = $params;

        if (preg_match('/(^.*)@/', $user, $matches)) {
            $this->params['username'] = $matches[1];
        } else {
            $this->params['username'] = $user;
        }
        $this->params['password'] = $password;

        $this->_imsp = &Net_IMSP::singleton('Options', $this->params);
        $result = $this->_imsp->init();
        if (is_a($result,'PEAR_Error')) {
            Horde::fatal($result, __FILE__, __LINE__);
        }
        $this->_imsp->setLogger($conf['log']);
    }

    /**
     * Retrieves the requested set of preferences from the IMSP server.
     *
     * @access public
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function retrieve()
    {
        // Get the defaults.
        parent::retrieve();

        // Get the shared prefs and remove the scope value from the
        // string.
        $global_prefs = $this->_imsp->get('horde.*');
        if (is_a($global_prefs, 'PEAR_Error')) {
            return $global_prefs;
        }

        foreach ($global_prefs as $key => $val) {
            $newKey = str_replace('horde.', '', $key);
            if ($val == '-') {
                $val = $this->getDefault($newKey);
            }

            if (isset($this->_prefs[$newKey])) {
                $this->setValue($newKey, $val);
            } else {
                $this->add($newKey, $val, _PREF_SHARED);
            }

            // Don't forget to clean it.
            $this->setDirty($newKey, false);
        }

        // Now the app specific prefs.
        $local_prefs = $this->_imsp->get($this->_scope . '.*');
        if (is_a($local_prefs, 'PEAR_Error')) {
            return $local_prefs;
        }

        foreach ($local_prefs as $key => $val) {
            $newKey = str_replace($this->_scope . '.' , '', $key);
            if ($val == '-') {
                $val = $this->getDefault($newKey);
            }
            if (isset($this->_prefs[$newKey])) {
                $this->setValue($newKey, $val);
            } else {
                $this->add($newKey, $val, 0);
            }

            // Clean the pref.
            $this->setDirty($newKey, false);
        }

        $_SESSION['prefs_cache']['_filled']['horde'] = true;
        $_SESSION['prefs_cache']['_filled'][$this->_scope] = true;
        $this->_callHooks();
        $this->cacheUpdate();
        return true;
    }

    /**
     * Stores all dirty prefs to IMSP server.
     *
     * @access public
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function store()
    {
        $dirty_prefs = $this->_dirtyPrefs();
        if (!count($dirty_prefs)) {
            return true;
        }

        foreach ($dirty_prefs as $name) {
            $scope = $this->getScope($name);
            $value = $this->getValue($name);
            if (empty($value)) {
                $value = '-';
            }

            $result = $this->_imsp->set($scope . '.' . $name, $value);
            if (is_a($result, 'PEAR_Error')) {
                $GLOBALS['notification']->push("There was a problem saving the prefrences");
                return $result;
            }

            // Clean the pref since it was just saved.
            $this->setDirty($name, false);
        }

        $this->cacheUpdate();
        return true;
    }

}

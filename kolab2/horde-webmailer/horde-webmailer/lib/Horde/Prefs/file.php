<?php
/**
 * Preferences storage implementation using files in a directory
 *
 * $Horde: framework/Prefs/Prefs/file.php,v 1.1.2.4 2009-09-09 20:06:22 wrobel Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @since   Horde 3.2
 * @package Horde_Prefs
 */
class Prefs_file extends Prefs {

    /**
     * Current version number of the data format
     *
     * @var int
     */
    var $_version = 2;

    /**
     * Directory to store the preferences
     *
     * @var string
     */
    var $_dirname;

    /**
     * Full path to the current preference file
     *
     * @var string
     */
    var $_fullpath;

    /**
     * Cached unserialized data of all scopes
     *
     * @var array
     */
    var $_file_cache;

    /**
     * Constructs a new file preferences object.
     *
     * @param string $user      The user who owns these preferences.
     * @param string $password  The password associated with $user. (Unused)
     * @param string $scope     The current preferences scope.
     * @param array $params     A hash containing connection parameters.
     * @param boolean $caching  Should caching be used?
     *
     */
    function Prefs_file($user, $password = '', $scope = '',
                        $params = null, $caching = true)
    {
        $this->_user = $user;
        $this->_scope = $scope;
        $this->_caching = $caching;

        // Sanity check for directory
        $error = 0;
        if (empty($params['directory']) || !is_dir($params['directory'])) {
            Horde::logMessage(_("Preference storage directory is not available."), __FILE__, __LINE__, PEAR_LOG_ERR);
            $error = 1;
        }

        if (!$error && !is_writable($params['directory'])) {
            Horde::logMessage(sprintf(_("Directory %s is not writeable"), $params['directory']), __FILE__, __LINE__, PEAR_LOG_ERR);
            $error = 1;
        }

        if ($error) {
            $this->_dirname = null;
            $this->_fullpath = null;

            if (isset($GLOBALS['notification'])) {
                $GLOBALS['notification']->push(_("The preferences backend is currently unavailable and your preferences have not been loaded. You may continue to use the system with default settings."));
            }
        } else {
            $this->_dirname = $params['directory'];
            $this->_fullpath = $this->_dirname . '/' . basename($user) . '.prefs';
        }

        $this->_file_cache = null;

        parent::Prefs();
    }

    /**
     * Retrieves the requested set of preferences from the current session.
     *
     * @param $scope Scope specifier.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _retrieve($scope)
    {
        if ($this->_dirname === null) {
            return false;
        }

        if (!is_array($this->_file_cache)) {
            // Try to read
            $this->_file_cache = $this->_read_cache();
            if ($this->_file_cache === null) {
                return false;
            }

            // Check version number. We can call format transformations hooks
            // in the future.
            if (!is_array($this->_file_cache) ||
                !array_key_exists('__file_version', $this->_file_cache) ||
                !($this->_file_cache['__file_version'] == $this->_version)) {
                if ($this->_file_cache['__file_version'] == 1) {
                    $this->transformV1V2();
                } else {
                    return PEAR::raiseError(sprintf(_("Wrong version number found: %s (should be %d)"),
                                                    $this->_file_cache['__file_version'], $this->_version));
                }
            }
        }

        // Check if the scope exists
        if (empty($scope) || !array_key_exists($scope, $this->_file_cache)) {
            return false;
        }

        // Merge config values
        foreach ($this->_file_cache[$scope] as $name => $val) {
            if (isset($this->_scopes[$scope][$name])) {
                $this->_scopes[$scope][$name]['v'] = $val;
                $this->_scopes[$scope][$name]['m'] &= ~_PREF_DEFAULT;
            } else {
                // This is a shared preference.
                $this->_scopes[$scope][$name] = array('v' => $val,
                                                      'm' => 0,
                                                      'd' => null);
            }
        }

        return true;
    }

    /**
     * Read data from disc
     *
     * @return mixed  data array on success or a null on error.
     */
    function _read_cache()
    {
        if (!file_exists($this->_fullpath)) {
            return null;
        }

        return unserialize(file_get_contents($this->_fullpath));
    }

    /**
     * Transforms the broken version 1 format into version 2.
     *
     * @return NULL
     */
    function transformV1V2()
    {
        $version2 = array('__file_version' => 2);
        foreach ($this->_file_cache as $scope => $prefs) {
            if ($scope == '__file_version') {
                continue;
            }
            foreach ($prefs as $name => $pref) {
                /**
                 * Default values should not have been stored by the
                 * driver. They are being set via the prefs.php files.
                 */
                if ($pref['m'] & _PREF_DEFAULT) {
                    continue;
                }
                $version2[$scope][$name] = $pref['v'];
            }
        }
        $this->_file_cache = $version2;
    }

    /**
     * Write data to disc
     *
     * @return mixed  True on success or a false on error.
     */
    function _write_cache()
    {
        require_once 'Horde/Util.php';
        $tmp_file = Util::getTempFile('PrefsFile', true, $this->_dirname);

        $data = serialize($this->_file_cache);

        if (function_exists('file_put_contents')) {
            if (file_put_contents($tmp_file, $data) === false) {
                return false;
            }
        } elseif ($fd = fopen($tmp_file, 'w')) {
            $res = fwrite($fd, $data);
            fclose($fd);
            if ($res < strlen($data)) {
                return false;
            }
        } else {
            return false;
        }

        return @rename($tmp_file, $this->_fullpath);
    }

    /**
     * Stores preferences in the current session.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function store()
    {
        if ($this->_dirname === null) {
            return false;
        }

        // Get the list of preferences that have changed. If there are
        // none, no need to hit the backend.
        $dirty_prefs = $this->_dirtyPrefs();
        if (!$dirty_prefs) {
            return true;
        }

        // Read in all existing preferences, if any.
        $this->_retrieve('');
        if (!is_array($this->_file_cache)) {
            $this->_file_cache = array('__file_version' => $this->_version);
        }

        // Update all values from dirty scope
        foreach ($dirty_prefs as $scope => $prefs) {
            foreach ($prefs as $name => $pref) {
                // Don't store locked preferences.
                if ($this->_scopes[$scope][$name]['m'] & _PREF_LOCKED) {
                    continue;
                }

                $this->_file_cache[$scope][$name] = $pref['v'];

                // Clean the pref since it was just saved.
                $this->_scopes[$scope][$name]['m'] &= ~_PREF_DIRTY;
            }
        }

        if ($this->_write_cache() == false) {
            return PEAR::raiseError(sprintf(_("Write of preferences to %s failed"),
                                            $this->_filename));
        }

        return true;
    }

}

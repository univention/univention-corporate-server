<?php
/**
 * $Horde: framework/Prefs/Prefs.php,v 1.137.10.42 2009-06-04 19:00:36 mrubinsk Exp $
 */

/** Preference is administratively locked. */
define('_PREF_LOCKED', 1);

/** Preference is shared amongst applications. */
define('_PREF_SHARED', 2);

/** Preference value has been changed. */
define('_PREF_DIRTY', 4);

/** Preference value is the application default. */
define('_PREF_DEFAULT', 8);

/**
 * The Prefs:: class provides a common abstracted interface into the
 * various preferences storage mediums.  It also includes all of the
 * functions for retrieving, storing, and checking preference values.
 *
 * TODO: document the format of the $_prefs hash here
 *
 * $_prefs[*pref name*] = array(
 *     'value'  => *Default value*,
 *     'locked' => *boolean*,
 *     'shared' => *boolean*,
 *     'type'   => 'checkbox'
 *                 'text'
 *                 'password'
 *                 'textarea'
 *                 'select'
 *                 'number'
 *                 'implicit'
 *                 'special'
 *                 'link' - There must be a field named either 'url'
 *                          (internal application link) or 'xurl'
 *                          (external application link) if this type is used.
 *                 'enum'
 *     'enum'   => TODO,
 *     'desc'   => _(*Description string*),
 *     'help'   => *Name of the entry in the XML help file*
 * );
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 1.3
 * @package Horde_Prefs
 */
class Prefs {

    /**
     * Hash holding the current set of preferences. Each preference is
     * itself a hash, so this will ultimately be multi-dimensional.
     *
     * [*pref name*] => Array(
     *     [d]  =>  *default value*
     *     [m]  =>  *pref mask*
     *     [v]  =>  *pref value*
     * )
     *
     * @var array
     */
    var $_prefs = array();

    /**
     * String containing the name of the current scope. This is used
     * to differentiate between sets of preferences (multiple
     * applications can have a "sortby" preference, for example). By
     * default, all preferences belong to the "global" (Horde) scope.
     *
     * @var string
     */
    var $_scope = 'horde';

    /**
     * Array of loaded scopes. In order to only load what we need, and
     * to not load things multiple times, we need to maintain a list
     * of loaded scopes. $this->_prefs will always be the combination
     * of the current scope and the 'horde' scope (or just the 'horde'
     * scope).
     *
     * @var array
     */
    var $_scopes = array();

    /**
     * String containing the current username. This indicates the owner of the
     * preferences.
     *
     * @var string
     */
    var $_user = '';

    /**
     * Boolean indicating whether preference caching should be used.
     *
     * @var boolean
     */
    var $_caching = false;

    /**
     * Array to cache in. Usually a reference to an array in $_SESSION, but
     * could be overridden by a subclass for testing or other users.
     *
     * @var array
     */
    var $_cache;

    /**
     * Hash holding preferences with hook functions defined.
     *
     * @var array
     */
    var $_hooks = array();

    /**
     * Default constructor (must be called from each extending class in their
     * constructors via parent::Prefs()).
     */
    function Prefs()
    {
        $this->_shutdown();

        // Create a unique key that's safe to use for caching even if we want
        // another user's preferences later, then register the cache array in
        // $_SESSION.
        if ($this->_caching) {
            $cacheKey = 'horde_prefs_' . sha1(serialize(array($this->_user)));
            if (!isset($_SESSION[$cacheKey])) {
                $_SESSION[$cacheKey] = array();
            }

            // Store a reference to the $_SESSION array.
            $this->_cache = &$_SESSION[$cacheKey];
        }
    }

    /**
     * Register the shutdown function.
     *
     * @access private
     */
    function _shutdown()
    {
        register_shutdown_function(array(&$this, 'store'));
    }

    /**
     * Returns the charset used by the concrete preference backend.
     *
     * @return string  The preference backend's charset.
     */
    function getCharset()
    {
        return NLS::getCharset();
    }

    /**
     * Return the user who owns these preferences.
     *
     * @return string  The user these preferences are for.
     */
    function getUser()
    {
        return $this->_user;
    }

    /**
     * Get the current scope
     *
     * @return string The current scope (application)
     *
     * @since Horde 3.2
     */
    function getScope()
    {
        return $this->_scope;
    }

    /**
     * Change scope without explicitly retrieving preferences
     *
     * @param string $scope The new scope.
     *
     * @since Horde 3.2
     */
    function setScope($scope)
    {
        $this->_scope = $scope;
    }

    /**
     * Removes a preference entry from the $prefs hash.
     *
     * @param string $pref  The name of the preference to remove.
     */
    function remove($pref)
    {
        // FIXME not updated yet.
        $scope = $this->_getPreferenceScope($pref);
        unset($this->_prefs[$pref]);
        unset($this->_cache[$scope][$pref]);
    }

    /**
     * Sets the given preferences ($pref) to the specified value
     * ($val), if the preference is modifiable.
     *
     * @param string $pref      The name of the preference to modify.
     * @param string $val       The new value for this preference.
     * @param boolean $convert  If true the preference value gets converted
     *                          from the current charset to the backend's
     *                          charset.
     *
     * @return boolean  True if the value was successfully set, false on a
     *                  failure.
     */
    function setValue($pref, $val, $convert = true)
    {
        /* Exit early if this preference is locked or doesn't exist. */
        if (!isset($this->_prefs[$pref]) || $this->isLocked($pref)) {
            return false;
        }

        $result = $this->_setValue($pref, $val, true, $convert);
        if ($result && $this->isDirty($pref)) {
            $this->_cacheUpdate($this->_getPreferenceScope($pref), array($pref));

            /* If this preference has a change hook, call it now. */
            Horde::callHook('_prefs_change_hook_' . $pref);
        }

        return $result;
    }

    function __set($name, $value)
    {
        return $this->setValue($name, $value);
    }

    /**
     * Sets the given preferences ($pref) to the specified value
     * ($val), whether or not the preference is user-modifiable, unset
     * the default bit, and set the dirty bit.
     *
     * @access protected
     *
     * @param string  $pref     The name of the preference to modify.
     * @param string  $val      The new value for this preference.
     * @param boolean $dirty    True if we should mark the new value as
     *                          dirty (changed).
     * @param boolean $convert  If true the preference value gets converted
     *                          from the current charset to the backend's
     *                          charset.
     *
     * @return boolean  True if the value was successfully set, false on a
     *                  failure.
     */
    function _setValue($pref, $val, $dirty = true, $convert = true)
    {
        global $conf;

        if ($convert) {
            $val = $this->convertToDriver($val, NLS::getCharset());
        }

        // If the preference's value is already equal to $val, don't
        // bother changing it. Changing it would set the "dirty" bit,
        // causing an unnecessary update later.
        if (isset($this->_prefs[$pref]) &&
            (($this->_prefs[$pref]['v'] == $val) &&
             !$this->isDefault($pref))) {
            return true;
        }

        // Check to see if the value exceeds the allowable storage
        // limit.
        if (isset($conf['prefs']['maxsize'])) {
            if (strlen($val) > $conf['prefs']['maxsize']) {
                global $notification;
                if (isset($notification)) {
                    $notification->push(sprintf(_("The preference \"%s\" could not be saved because its data exceeded the maximum allowable size"), $pref), 'horde.error');
                    return false;
                }
            }
        }

        // Assign the new value, unset the "default" bit, and set the
        // "dirty" bit.
        if (empty($this->_prefs[$pref]['m'])) {
            $this->_prefs[$pref]['m'] = 0;
        }
        $this->_prefs[$pref]['v'] = $val;
        $this->setDefault($pref, false);
        if ($dirty) {
            $this->setDirty($pref, true);
        }

        // Finally, copy into the $_scopes array.
        $this->_scopes[$this->_getPreferenceScope($pref)][$pref] = $this->_prefs[$pref];

        return true;
    }

    /**
     * Returns the value of the requested preference.
     *
     * @param string $pref      The name of the preference to retrieve.
     * @param boolean $convert  If true the preference value gets converted
     *                          from the backend's charset to the current
     *                          charset.
     *
     * @return string  The value of the preference, null if it doesn't exist.
     */
    function getValue($pref, $convert = true)
    {
        static $charset;
        if (!isset($charset)) {
            $charset = NLS::getCharset();
        }

        if (isset($this->_prefs[$pref]['v'])) {
            if ($convert) {
                if ($this->isDefault($pref)) {
                    /* Default values have the current UI charset. */
                    $value = String::convertCharset($this->_prefs[$pref]['v'], NLS::getCharset(), $charset);
                } else {
                    /* Stored values have the backend charset. */
                    $value = $this->convertFromDriver($this->_prefs[$pref]['v'], $charset);
                }
            } else {
                $value = $this->_prefs[$pref]['v'];
            }
        } else {
            $value = null;
        }

        return $value;
    }

    function __get($name)
    {
        return $this->getValue($name);
    }

    /**
     * Modifies the "locked" bit for the given preference.
     *
     * @param string $pref   The name of the preference to modify.
     * @param boolean $bool  The new boolean value for the "locked" bit.
     */
    function setLocked($pref, $bool)
    {
        $this->_setMask($pref, $bool, _PREF_LOCKED);
    }

    /**
     * Returns the state of the "locked" bit for the given preference.
     *
     * @param string $pref  The name of the preference to check.
     *
     * @return boolean  The boolean state of $pref's "locked" bit.
     */
    function isLocked($pref)
    {
        return $this->_getMask($pref, _PREF_LOCKED);
    }

    /**
     * Modifies the "shared" bit for the given preference.
     *
     * @param string $pref   The name of the preference to modify.
     * @param boolean $bool  The new boolean value for the "shared" bit.
     */
    function setShared($pref, $bool)
    {
        $this->_setMask($pref, $bool, _PREF_SHARED);
    }

    /**
     * Returns the state of the "shared" bit for the given preference.
     *
     * @param string $pref  The name of the preference to check.
     *
     * @return boolean  The boolean state of $pref's "shared" bit.
     */
    function isShared($pref)
    {
        return $this->_getMask($pref, _PREF_SHARED);
    }

    /**
     * Modifies the "dirty" bit for the given preference.
     *
     * @param string $pref      The name of the preference to modify.
     * @param boolean $bool     The new boolean value for the "dirty" bit.
     */
    function setDirty($pref, $bool)
    {
        $this->_setMask($pref, $bool, _PREF_DIRTY);
    }

    /**
     * Returns the state of the "dirty" bit for the given preference.
     *
     * @param string $pref  The name of the preference to check.
     *
     * @return boolean  The boolean state of $pref's "dirty" bit.
     */
    function isDirty($pref)
    {
        return $this->_getMask($pref, _PREF_DIRTY);
    }

    /**
     * Modifies the "default" bit for the given preference.
     *
     * @param string $pref   The name of the preference to modify.
     * @param boolean $bool  The new boolean value for the "default" bit.
     */
    function setDefault($pref, $bool)
    {
        $this->_setMask($pref, $bool, _PREF_DEFAULT);
    }

    /**
     * Returns the default value of the given preference.
     *
     * @param string $pref  The name of the preference to get the default for.
     *
     * @return string  The preference's default value.
     */
    function getDefault($pref)
    {
        return !empty($this->_prefs[$pref]['d']) ?
            $this->_prefs[$pref]['d'] :
            '';
    }

    /**
     * Determines if the current preference value is the default
     * value from prefs.php or a user defined value
     *
     * @param string $pref  The name of the preference to check.
     *
     * @return boolean  True if the preference is the application default
     *                  value.
     */
    function isDefault($pref)
    {
        return $this->_getMask($pref, _PREF_DEFAULT);
    }

    /**
     * Sets the value for a given mask.
     *
     * @access private
     *
     * @param string $pref   The name of the preference to modify.
     * @param boolean $bool  The new boolean value for the "default" bit.
     * @param integer $mask  The mask to add.
     */
    function _setMask($pref, $bool, $mask)
    {
        if (isset($this->_prefs[$pref])) {
            if ($bool != $this->_getMask($pref, $mask)) {
                if ($bool) {
                    $this->_prefs[$pref]['m'] |= $mask;
                } else {
                    $this->_prefs[$pref]['m'] &= ~$mask;
                }
            }
        }
    }

    /**
     * Gets the boolean state for a given mask.
     *
     * @access private
     *
     * @param string $pref   The name of the preference to modify.
     * @param integer $mask  The mask to get.
     *
     * @return boolean  The boolean state for the given mask.
     */
    function _getMask($pref, $mask)
    {
        return isset($this->_prefs[$pref]['m']) ? (bool)($this->_prefs[$pref]['m'] & $mask) : false;
    }

    /**
     * Returns the scope of the given preference.
     *
     * @access protected
     *
     * @param string $pref  The name of the preference to examine.
     *
     * @return string  The scope of the $pref.
     */
    function _getPreferenceScope($pref)
    {
        if ($this->isShared($pref)) {
            return 'horde';
        } else {
            return $this->_scope;
        }
    }

    /**
     * Retrieves preferences for the current scope + the 'horde'
     * scope.
     *
     * @param $scope Optional scope specifier - if not present the
     * current scope will be used.
     */
    function retrieve($scope = null)
    {
        if ($scope === null) {
            $scope = $this->_scope;
        } else {
            $this->_scope = $scope;
        }

        $this->_loadScope('horde');
        if ($scope != 'horde') {
            $this->_loadScope($scope);
        }

        if ($scope == 'horde') {
            $this->_prefs = $this->_scopes['horde'];
        } else {
            $this->_prefs = array_merge($this->_scopes['horde'], $this->_scopes[$scope]);
        }
    }

    /**
     * Load a specific preference scope.
     */
    function _loadScope($scope)
    {
        // Return if we've already loaded these prefs.
        if (!empty($this->_scopes[$scope])) {
            return;
        }

        // Basic initialization so _something_ is always set.
        $this->_scopes[$scope] = array();

        // Always set defaults to pick up new default values, etc.
        $this->_setDefaults($scope);

        // Now check the prefs cache for existing values.
        if ($this->_cacheLookup($scope)) {
            return;
        }

        $this->_retrieve($scope);
        $this->_callHooks($scope);

        /* Update the session cache. */
        $this->_cacheUpdate($scope, array_keys($this->_scopes[$scope]));
    }

    /**
     * This function will be run at the end of every request as a shutdown
     * function (registered by the Prefs:: constructor).  All prefs with the
     * dirty bit set will be saved to the storage backend at this time; thus,
     * there is no need to manually call $prefs->store() every time a
     * preference is changed.
     *
     * @abstract
     */
    function store()
    {
    }

    /**
     * This function provides common cleanup functions for all of the driver
     * implementations.
     *
     * @param boolean $all  Clean up all Horde preferences.
     */
    function cleanup($all = false)
    {
        /* Perform a Horde-wide cleanup? */
        if ($all) {
            /* Destroy the contents of the preferences hash. */
            $this->_prefs = array();

            /* Destroy the contents of the preferences cache. */
            unset($this->_cache);
        } else {
            /* Remove this scope from the preferences cache, if it exists. */
            unset($this->_cache[$this->_scope]);
        }
    }

    /**
     * Clears all preferences from the backend.
     */
    function clear()
    {
        $this->cleanup(true);
    }

    /**
     * Converts a value from the driver's charset to the specified charset.
     *
     * @param mixed $value     A value to convert.
     * @param string $charset  The charset to convert to.
     *
     * @return mixed  The converted value.
     */
    function convertFromDriver($value, $charset)
    {
        return $value;
    }

    /**
     * Converts a value from the specified charset to the driver's charset.
     *
     * @param mixed $value  A value to convert.
     * @param string $charset  The charset to convert from.
     *
     * @return mixed  The converted value.
     */
    function convertToDriver($value, $charset)
    {
        return $value;
    }

    /**
     * Return all "dirty" preferences across all scopes.
     *
     * @access protected
     *
     * @return array The values for all dirty preferences, in a
     * multi-dimensional array of scope => pref name => pref values.
     */
    function _dirtyPrefs()
    {
        $dirty_prefs = array();

        foreach ($this->_scopes as $scope => $prefs) {
            foreach ($prefs as $pref_name => $pref) {
                if (isset($pref['m']) && ($pref['m'] & _PREF_DIRTY)) {
                    $dirty_prefs[$scope][$pref_name] = $pref;
                }
            }
        }

        return $dirty_prefs;
    }

    /**
     * Updates the session-based preferences cache (if available).
     *
     * @access protected
     *
     * @param string $scope The scope of the prefs being updated.
     * @param array $prefs  The preferences to update.
     */
    function _cacheUpdate($scope, $prefs)
    {
        /* Return immediately if caching is disabled. */
        if (!$this->_caching) {
            return;
        }

        if (isset($this->_cache)) {
            /* Place each preference in the cache according to its
             * scope. */
            foreach ($prefs as $name) {
                if (isset($this->_scopes[$scope][$name])) {
                    $this->_cache[$scope][$name] = $this->_scopes[$scope][$name];
                }
            }
        }
    }

    /**
     * Tries to find the requested preferences in the cache. If they
     * exist, update the $_scopes hash with the cached values.
     *
     * @access protected
     *
     * @return boolean  True on success, false on failure.
     */
    function _cacheLookup($scope)
    {
        /* Return immediately if caching is disabled. */
        if (!$this->_caching) {
            return false;
        }

        if (isset($this->_cache[$scope])) {
            $this->_scopes[$scope] = $this->_cache[$scope];
            return true;
        }

        return false;
    }

    /**
     * Populates the $_scopes hash with new entries and externally
     * defined default values.
     *
     * @access private
     *
     * @param string $scope  The scope to load defaults for.
     */
    function _setDefaults($scope)
    {
        /* Read the configuration file. The $_prefs array is assumed to hold
         * the default values. */
        $result = Horde::loadConfiguration('prefs.php', array('_prefs'), $scope);
        if (is_a($result, 'PEAR_Error') || empty($result)) {
            return;
        }
        extract($result);

        foreach ($_prefs as $name => $pref) {
            if (isset($pref['value']) &&
                isset($pref['locked']) &&
                isset($pref['shared']) &&
                ($pref['type'] != 'link') &&
                ($pref['type'] != 'special')) {
                $name = str_replace('.', '_', $name);

                $mask = 0;
                $mask &= ~_PREF_DIRTY;
                $mask |= _PREF_DEFAULT;

                if ($pref['locked']) {
                    $mask |= _PREF_LOCKED;
                }

                if ($pref['shared'] || ($scope == 'horde')) {
                    $mask |= _PREF_SHARED;
                    $pref_scope = 'horde';
                } else {
                    $pref_scope = $scope;
                }

                if ($pref['shared'] && isset($this->_scopes[$pref_scope][$name])) {
                    // This is a shared preference that was already
                    // retrieved.
                    $this->_scopes[$pref_scope][$name]['m'] = $mask & ~_PREF_DEFAULT;
                    $this->_scopes[$pref_scope][$name]['d'] = $pref['value'];
                } else {
                    $this->_scopes[$pref_scope][$name] = array('v' => $pref['value'], 'm' => $mask, 'd' => $pref['value']);
                }

                if (!empty($pref['hook'])) {
                    if (!isset($this->_hooks[$scope])) {
                        $this->_hooks[$scope] = array();
                    }
                    $this->_hooks[$scope][$name] = $pref_scope;
                }
            }
        }
    }

    /**
     * After preferences have been loaded, set any locked or empty
     * preferences that have hooks to the result of the hook.
     *
     * @param string $scope The preferences scope to call hooks for.
     *
     * @access private
     */
    function _callHooks($scope)
    {
        if (empty($this->_hooks[$scope])) {
            return;
        }

        foreach ($this->_hooks[$scope] as $name => $pref_scope) {
            if ($this->_scopes[$pref_scope][$name]['m'] & _PREF_LOCKED ||
                empty($this->_scopes[$pref_scope][$name]['v']) ||
                $this->_scopes[$pref_scope][$name]['m'] & _PREF_DEFAULT) {

                $val = Horde::callHook('_prefs_hook_' . $name, array($this->_user), $scope, $name);
                if (is_a($val, 'PEAR_Error')) {
                    Horde::logMessage($val, __FILE__, __LINE__, PEAR_LOG_ERR);
                    continue;
                }

                if ($this->_scopes[$pref_scope][$name]['m'] & _PREF_DEFAULT) {
                    $this->_scopes[$pref_scope][$name]['v'] = $val;
                } else {
                    $this->_scopes[$pref_scope][$name]['v'] = $this->convertToDriver($val, NLS::getCharset());
                }
                if (!($this->_scopes[$pref_scope][$name]['m'] & _PREF_LOCKED)) {
                    $this->_scopes[$pref_scope][$name]['m'] |= _PREF_DIRTY;
                }
            }
        }
    }

    /**
     * Attempts to return a concrete Prefs instance based on $driver.
     *
     * @param mixed $driver     The type of concrete Prefs subclass to return.
     * @param string $scope     The scope for this set of preferences.
     * @param string $user      The name of the user who owns this set of
     *                          preferences.
     * @param string $password  The password associated with $user.
     * @param array $params     A hash containing any additional configuration
     *                          or connection parameters a subclass might need.
     * @param boolean $caching  Should caching be used?
     *
     * @return Prefs  The newly created concrete Prefs instance, or false on
     *                error.
     */
    function &factory($driver, $scope = 'horde', $user = '', $password = '',
                      $params = null, $caching = true)
    {
        $driver = basename($driver);
        if (empty($driver) || $driver == 'none') {
            $driver = 'session';
        }

        if (is_null($params)) {
            $params = Horde::getDriverConfig('prefs', $driver);
        }

        /* If $params['user_hook'] is defined, use it to retrieve the value to
         * use for the username ($this->_user). Otherwise, just use the value
         * passed in the $user parameter. */
        if (!empty($params['user_hook']) &&
            function_exists($params['user_hook'])) {
            $user = call_user_func($params['user_hook'], $user);
        }

        $class = 'Prefs_' . $driver;
        if (!class_exists($class)) {
            include 'Horde/Prefs/' . $driver . '.php';
        }
        if (class_exists($class)) {
            $prefs = &new $class($user, $password, $scope, $params, $caching);
            $prefs->retrieve($scope);
        } else {
            $prefs = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $prefs;
    }

    /**
     * Attempts to return a reference to a concrete Prefs instance based on
     * $driver. It will only create a new instance if no Prefs instance
     * with the same parameters currently exists.
     *
     * This should be used if multiple preference sources (and, thus,
     * multiple Prefs instances) are required.
     *
     * This method must be invoked as: $var = &Prefs::singleton()
     *
     * @param mixed $driver     The type of concrete Prefs subclass to return.
     *                          If $driver is an array, then we will look in
     *                          $driver[0]/lib/Prefs/ for the subclass
     *                          implementation named $driver[1].php.
     * @param string $scope     The scope for this set of preferences.
     * @param string $user      The name of the user who owns this set of
     *                          preferences.
     * @param string $password  The password associated with $user.
     * @param array $params     A hash containing any additional configuration
     *                          or connection parameters a subclass might need.
     * @param boolean $caching  Should caching be used?
     *
     * @return Prefs  The concrete Prefs reference, or false on an error.
     */
    function &singleton($driver, $scope = 'horde', $user = '', $password = '',
                        $params = null, $caching = true)
    {
        static $instances = array();

        if (is_null($params)) {
            $params = Horde::getDriverConfig('prefs', $driver);
        }

        $signature = serialize(array($driver, $user, $params, $caching));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Prefs::factory($driver, $scope, $user, $password, $params, $caching);
        }

        /* Preferences may be cached with a different scope. */
        $instances[$signature]->setScope($scope);

        return $instances[$signature];
    }

}

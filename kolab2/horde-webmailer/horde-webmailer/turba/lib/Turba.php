<?php
/**
 * $Horde: turba/lib/Turba.php,v 1.59.4.46 2009-10-26 17:34:16 jan Exp $
 *
 * @package Turba
 */

/** The virtual path to use for VFS data. */
define('TURBA_VFS_PATH', '.horde/turba/documents');

/**
 * Turba Base Class.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @package Turba
 */
class Turba {

    function formatEmailAddresses($data, $name)
    {
        global $registry;
        static $batchCompose;

        if (!isset($batchCompose)) {
            $batchCompose = $registry->hasMethod('mail/batchCompose');
        }

        require_once 'Horde/MIME.php';

        $array = is_array($data);
        if (!$array) {
            $data = array($data);
        }

        $addresses = array();
        foreach ($data as $i => $email_vals) {
            $email_vals = explode(',', $email_vals);
            foreach ($email_vals as $j => $email_val) {
                $email_val = trim($email_val);

                // Format the address according to RFC822.
                $mailbox_host = explode('@', $email_val);
                if (!isset($mailbox_host[1])) {
                    $mailbox_host[1] = '';
                }

                $address = MIME::rfc822WriteAddress($mailbox_host[0], $mailbox_host[1], $name);

                // Get rid of the trailing @ (when no host is included in
                // the email address).
                $addresses[$i . ':' . $j] = array('to' => addslashes(str_replace('@>', '>', $address)));
                if (!$batchCompose) {
                    $addresses[$i . ':' . $j] = $GLOBALS['registry']->call('mail/compose', $addresses[$i . ':' . $j]);
                }
            }
        }

        if ($batchCompose) {
            $addresses = $GLOBALS['registry']->call('mail/batchCompose', array($addresses));
        }

        foreach ($data as $i => $email_vals) {
            $email_vals = explode(',', $email_vals);
            $email_values = false;
            foreach ($email_vals as $j => $email_val) {
                if (!is_a($addresses, 'PEAR_Error')) {
                    $mail_link = $addresses[$i . ':' . $j];
                    if (is_a($mail_link, 'PEAR_Error')) {
                        $mail_link = 'mailto:' . urlencode($email_val);
                    }
                } else {
                    $mail_link = 'mailto:' . urlencode($email_val);
                }

                $email_value = Horde::link($mail_link) . htmlspecialchars($email_val) . '</a>';
                if ($email_values) {
                    $email_values .= ', ' . $email_value;
                } else {
                    $email_values = $email_value;
                }
            }
        }

        if ($array) {
            return $email_values[0];
        } else {
            return $email_values;
        }
    }

    /**
     * Get all the address books the user has the requested permissions to and
     * return them in the user's preferred order.
     *
     * @param integer $permission  The PERMS_* constant to filter on.
     * @param array $options       Any additional options.
     *
     * @return array  The filtered, ordered $cfgSources entries.
     */
    function getAddressBooks($permission = PERMS_READ, $options = array())
    {
        $addressbooks = array();
        foreach (array_keys(Turba::getAddressBookOrder()) as $addressbook) {
            $addressbooks[$addressbook] = $GLOBALS['cfgSources'][$addressbook];
        }

        if (!$addressbooks) {
            $addressbooks = $GLOBALS['cfgSources'];
        }

        return Turba::permissionsFilter($addressbooks, $permission, $options);
    }

    /**
     * Get the order the user selected for displaying address books.
     *
     * @return array  An array describing the order to display the address books.
     */
    function getAddressBookOrder()
    {
        $i = 0;
        $lines = explode("\n", $GLOBALS['prefs']->getValue('addressbooks'));
        $temp = $lines;
        $addressbooks = array();
        foreach ($lines as $line) {
            $line = trim($line);
            if ($line && isset($GLOBALS['cfgSources'][$line])) {
                $addressbooks[$line] = $i++;
            }
        }
        return $addressbooks;
    }

    /**
     * Returns the current user's default address book.
     *
     * @return string  The default address book name.
     */
    function getDefaultAddressBook()
    {
        $lines = explode("\n", $GLOBALS['prefs']->getValue('addressbooks'));
        foreach ($lines as $line) {
            $line = trim($line);
            if ($line && isset($GLOBALS['cfgSources'][$line])) {
                return $line;
            }
        }

        reset($GLOBALS['cfgSources']);
        return key($GLOBALS['cfgSources']);
    }

    /**
     * Returns the sort order selected by the user
     */
    function getPreferredSortOrder()
    {
        return @unserialize($GLOBALS['prefs']->getValue('sortorder'));
    }

    /**
     * Retrieves a column's field name
     */
    function getColumnName($i, $columns)
    {
        return $i == 0 ? 'name' : $columns[$i - 1];
    }

    /**
     */
    function getColumns()
    {
        $columns = array();
        $lines = explode("\n", $GLOBALS['prefs']->getValue('columns'));
        foreach ($lines as $line) {
            $line = trim($line);
            if ($line) {
                $cols = explode("\t", $line);
                if (count($cols) > 1) {
                    $source = array_splice($cols, 0, 1);
                    $columns[$source[0]] = $cols;
                }
            }
        }

        return $columns;
    }

    /**
     * Returns a best guess at the lastname in a string.
     *
     * @param string $name  String contain the full name.
     *
     * @return string  String containing the last name.
     */
    function guessLastname($name)
    {
        $name = trim(preg_replace('|\s|', ' ', $name));
        if (!empty($name)) {
            /* Assume that last names are always before any commas. */
            if (is_int(strpos($name, ','))) {
                $name = String::substr($name, 0, strpos($name, ','));
            }

            /* Take out anything in parentheses. */
            $name = trim(preg_replace('|\(.*\)|', '', $name));

            $namelist = explode(' ', $name);
            $name = $namelist[($nameindex = (count($namelist) - 1))];

            while (!empty($name) && String::length($name) < 5 &&
                   strspn($name[(String::length($name) - 1)], '.:-') &&
                   !empty($namelist[($nameindex - 1)])) {
                $nameindex--;
                $name = $namelist[$nameindex];
            }
        }
        return strlen($name) ? $name : null;
    }

    /**
     * Formats the name according to the user's preference.
     *
     * @param Turba_Object $ob     The object to get a name from.
     * @param string $name_format  The formatting. One of 'none', 'last_first'
     *                             or 'first_last'.
     *
     * @return string  The formatted name, either "Firstname Lastname"
     *                 or "Lastname, Firstname" depending on $name_format or
     *                 the user's preference.
     */
    function formatName($ob, $name_format = null)
    {
        static $default_format;

        if (!$name_format) {
            if (!isset($default_format)) {
                $default_format = $GLOBALS['prefs']->getValue('name_format');
            }
            $name_format = $default_format;
        }

        /* if no formatting, return original name */
        if ($name_format != 'first_last' && $name_format != 'last_first') {
            return $ob->getValue('name');
        }

        /* See if we have the name fields split out explicitly. */
        if ($ob->hasValue('firstname') && $ob->hasValue('lastname')) {
            if ($name_format == 'last_first') {
                return $ob->getValue('lastname') . ', ' . $ob->getValue('firstname');
            } else {
                return $ob->getValue('firstname') . ' ' . $ob->getValue('lastname');
            }
        } else {
            /* One field, we'll have to guess. */
            $name = $ob->getValue('name');
            $lastname = Turba::guessLastname($name);
            if ($name_format == 'last_first' &&
                !is_int(strpos($name, ',')) &&
                String::length($name) > String::length($lastname)) {
                $name = preg_replace('/\s+' . preg_quote($lastname, '/') . '/', '', $name);
                $name = $lastname . ', ' . $name;
            }
            if ($name_format == 'first_last' &&
                is_int(strpos($name, ',')) &&
                String::length($name) > String::length($lastname)) {
                $name = preg_replace('/' . preg_quote($lastname, '/') . ',\s*/', '', $name);
                $name = $name . ' ' . $lastname;
            }
            return $name;
        }
    }

    /**
     * Returns the real name, if available, of a user.
     *
     * @since Turba 2.2
     */
    function getUserName($uid)
    {
        static $names = array();

        if (!isset($names[$uid])) {
            require_once 'Horde/Identity.php';
            $ident = &Identity::singleton('none', $uid);
            $ident->setDefault($ident->getDefault());
            $names[$uid] = $ident->getValue('fullname');
            if (empty($names[$uid])) {
                $names[$uid] = $uid;
            }
        }

        return $names[$uid];
    }

    /**
     * Gets extended permissions on an address book.
     *
     * @since Turba 2.1
     *
     * @param Turba_Driver $addressBook The address book to get extended permissions for.
     * @param string $permission  What extended permission to get.
     *
     * @return mixed  The requested extended permissions value, or true if it doesn't exist.
     */
    function getExtendedPermission($addressBook, $permission)
    {
        global $perms;

        // We want to check the base source as extended permissions
        // are enforced per backend, not per share.
        $key = $addressBook->name . ':' . $permission;

        if (!$GLOBALS['perms']->exists('turba:sources:' . $key)) {
            return true;
        }

        $allowed = $GLOBALS['perms']->getPermissions('turba:sources:' . $key);
        if (is_array($allowed)) {
            switch ($permission) {
            case 'max_contacts':
                $allowed = max($allowed);
                break;
            }
        }
        return $allowed;
    }

    /**
     * Filters data based on permissions.
     *
     * @param array $in            The data we want filtered.
     * @param string $filter       What type of data we are filtering.
     * @param integer $permission  The PERMS_* constant we will filter on.
     * @param array $options       Additional options.
     *
     * @return array  The filtered data.
     */
    function permissionsFilter($in, $permission = PERMS_READ, $options = array())
    {
        $out = array();

        foreach ($in as $sourceId => $source) {
            $driver = &Turba_Driver::singleton($sourceId);
            if (is_a($driver, 'PEAR_Error')) {
                Horde::logMessage(sprintf("Could not instantiate the %s source: %s", $sourceId, $driver->getMessage()), __FILE__, __LINE__, PEAR_LOG_ERR);
                continue;
            }

            if ($driver->hasPermission($permission)) {
                if (!empty($options['require_add']) && !$driver->canAdd()) {
                    continue;
                }
                $out[$sourceId] = $source;
            }
        }

        return $out;
    }

    /**
     * Replaces all share-enabled sources in a source list with all shares
     * from this source that the current user has access to.
     *
     * This will only sync shares that are unique to Horde (basically, a SQL
     * driver source for now).  Any backend that supports ACLs or similar
     * mechanism should be configured from within sources.php or
     * _horde_hook_share_* calls.
     *
     * @param array $sources  The default $cfgSources array.
     *
     * @return array  The $cfgSources array.
     */
    function getConfigFromShares($sources)
    {
        global $notification;

        $shares = Turba::listShares();

        // Notify the user if we failed, but still return the $cfgSource array.
        if (is_a($shares, 'PEAR_Error')) {
            $notification->push($shares, 'horde.error');
            return $sources;
        }

        $sortedShares = $defaults = $vbooks = array();
        foreach (array_keys($shares) as $name) {
            if (isset($sources[$name])) {
                continue;
            }

            $params = @unserialize($shares[$name]->get('params'));
            if (isset($params['type']) && $params['type'] == 'vbook') {
                // We load vbooks last in case they're based on other shares.
                $params['share'] = &$shares[$name];
                $vbooks[$name] = $params;
            } elseif (!empty($params['source']) &&
                      !empty($sources[$params['source']]['use_shares'])) {
                if (empty($params['name'])) {
                    $params['name'] = $name;
                    $shares[$name]->set('params', serialize($params));
                    $shares[$name]->save();
                }

                // Default share?
                if (empty($defaults[$params['source']])) {
                    $driver = &Turba_Driver::singleton($params['source']);
                    if (!is_a($driver, 'PEAR_Error')) {
                        $defaults[$params['source']] =
                            $driver->checkDefaultShare(
                                $shares[$name],
                                $sources[$params['source']]);
                    } else {
                        $notification->push($driver, 'horde.error');
                    }
                }

                $share = $sources[$params['source']];
                $share['params']['config'] = $sources[$params['source']];
                $share['params']['config']['params']['share'] = &$shares[$name];
                $share['params']['config']['params']['name'] = $params['name'];
                $share['title'] = $shares[$name]->get('name');
                $share['type'] = 'share';
                $share['use_shares'] = false;
                $sortedSources[$params['source']][$name] = $share;
            }
        }

        // Check for the user's default share and built new source list.
        $newSources = array();
        foreach (array_keys($sources) as $source) {
            if (empty($sources[$source]['use_shares'])) {
                $newSources[$source] = $sources[$source];
                continue;
            }
            if (isset($sortedSources[$source])) {
                $newSources = array_merge($newSources, $sortedSources[$source]);
            }
            if (Auth::getAuth() && empty($defaults[$source])) {
                // User's default share is missing.
                $driver = &Turba_Driver::singleton($source);
                if (!is_a($driver, 'PEAR_Error')) {
                    $sourceKey = md5(mt_rand());
                    $share = &$driver->createShare(
                        $sourceKey,
                        array('params' => array('source' => $source,
                                                'default' => true,
                                                'name' => Auth::getAuth())));
                    if (is_a($share, 'PEAR_Error')) {
                        Horde::logMessage($share, __FILE__, __LINE__, PEAR_LOG_ERR);
                        continue;
                    }

                    $source_config = $sources[$source];
                    $source_config['params']['share'] = &$share;
                    $newSources[$sourceKey] = $source_config;
                } else {
                    $notification->push($driver, 'horde.error');
                }
            }
        }

        // Add vbooks now that all available address books are loaded.
        foreach ($vbooks as $name => $params) {
            $newSources[$name] = array(
                'title' => $shares[$name]->get('name'),
                'type' => 'vbook',
                'params' => $params,
                'export' => true,
                'browse' => true,
                'map' => $newSources[$params['source']]['map'],
                'search' => $newSources[$params['source']]['search'],
                'strict' => $newSources[$params['source']]['strict'],
                'use_shares' => false,
            );
        }

        return $newSources;
    }

    /**
     * Retrieve a new source config entry based on a Turba share.
     *
     * @param Horde_Share object  The share to base config on.
     *
     * @since Turba 2.2
     */
    function getSourceFromShare(&$share)
    {
        // Require a fresh config file.
        require TURBA_BASE . '/config/sources.php';

        $params = @unserialize($share->get('params'));
        $newConfig = $cfgSources[$params['source']];
        $newConfig['params']['config'] = $cfgSources[$params['source']];
        $newConfig['params']['config']['params']['share'] = &$share;
        $newConfig['params']['config']['params']['name'] = $params['name'];
        $newConfig['title'] = $share->get('name');
        $newConfig['type'] = 'share';
        $newConfig['use_shares'] = false;

        return $newConfig;
    }

    /**
     * Returns all shares the current user has specified permissions to.
     *
     * @param boolean $owneronly   Only return address books owned by the user?
     *                             Defaults to false.
     * @param integer $permission  Permissions to filter by.
     *
     * @return array  Shares the user has the requested permissions to.
     */
    function listShares($owneronly = false, $permission = PERMS_READ)
    {
        if (empty($_SESSION['turba']['has_share'])) {
            // No backends are configured to provide shares
            return array();
        }

        $sources = $GLOBALS['turba_shares']->listShares(
            Auth::getAuth(), $permission,
            $owneronly ? Auth::getAuth() : null);
        if (is_a($sources, 'PEAR_Error')) {
            Horde::logMessage($sources, __FILE__, __LINE__, PEAR_LOG_ERR);
            return array();
        }
        return $sources;
    }

    /**
     * Create a new Turba share.
     *
     * @param string $share_id The id for the new share.
     * @param array $params Parameters for the new share.
     *
     * @return mixed  The new share object or PEAR_Error
     */
    function &createShare($share_id, $params)
    {
        if (!isset($params['name'])) {
            /* Sensible default for empty display names */
            require_once 'Horde/Identity.php';
            $identity = &Identity::singleton();
            $name = $identity->getValue('fullname');
            if (trim($name) == '') {
                $name = Auth::removeHook(Auth::getAuth());
            }
            $name = sprintf(_("%s's Address Book"), $name);
        } else {
            $name = $params['name'];
            unset($params['name']);
        }

        /* Generate the new share. */
        $share = &$GLOBALS['turba_shares']->newShare($share_id);
        if (is_a($share, 'PEAR_Error')) {
            return $share;
        }

        /* Set the display name for this share. */
        $share->set('name', $name);

        /* Now any other params. */
        foreach ($params as $key => $value) {
            if (!is_scalar($value)) {
                $value = serialize($value);
            }
            $share->set($key, $value);
        }

        $result = $GLOBALS['turba_shares']->addShare($share);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $share->save();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Update share_id as backends like Kolab change it to the IMAP folder
         * name. */
        $share_id = $share->getName();

        /* Add the new addressbook to the user's list of visible address
         * books. */
        $prefs = $GLOBALS['prefs']->getValue('addressbooks');
        if ($prefs) {
            $prefs = explode("\n", $prefs);
            if (array_search($share_id, $prefs) === false) {
                $prefs[] = $share_id;
                $GLOBALS['prefs']->setValue('addressbooks', implode("\n", $prefs));
            }
        }

        return $share;
    }

    /**
     * Build Turba's list of menu items.
     */
    function getMenu($returnType = 'object')
    {
        require_once 'Horde/Menu.php';
        $menu = new Menu();

        if (!empty($_SESSION['turba']['has_share'])) {
            $menu->add(Horde::applicationUrl('addressbooks/index.php'), _("_My Address Books"), 'turba.png');
        }
        if ($GLOBALS['browse_source_count']) {
            $menu->add(Horde::applicationUrl('browse.php'), _("_Browse"), 'menu/browse.png', null, null, null, (($GLOBALS['prefs']->getValue('initial_page') == 'browse.php' && basename($_SERVER['PHP_SELF']) == 'index.php' && basename(dirname($_SERVER['PHP_SELF'])) != 'addressbooks') || (basename($_SERVER['PHP_SELF']) == 'browse.php' && Util::getFormData('key') != '**search')) ? 'current' : '__noselection');
        }
        if (count($GLOBALS['addSources'])) {
            $menu->add(Horde::applicationUrl('add.php'), _("_New Contact"), 'menu/new.png');
        }
        $menu->add(Horde::applicationUrl('search.php'), _("_Search"), 'search.png', $GLOBALS['registry']->getImageDir('horde'), null, null, (($GLOBALS['prefs']->getValue('initial_page') == 'search.php' && basename($_SERVER['PHP_SELF']) == 'index.php' && strpos($_SERVER['PHP_SELF'], 'addressbooks/index.php') === false) || (basename($_SERVER['PHP_SELF']) == 'browse.php' && Util::getFormData('key') == '**search')) ? 'current' : null);

        /* Import/Export */
        if ($GLOBALS['conf']['menu']['import_export']) {
            $menu->add(Horde::applicationUrl('data.php'), _("_Import/Export"), 'data.png', $GLOBALS['registry']->getImageDir('horde'));
        }

        /* Print. */
        if (isset($GLOBALS['print_link'])) {
            $menu->add($GLOBALS['print_link'], _("_Print"), 'print.png', $GLOBALS['registry']->getImageDir('horde'), '_blank', 'return !popup(this.href);', '__noselection');
        }

        if ($returnType == 'object') {
            return $menu;
        } else {
            return $menu->render();
        }
    }

    /**
     * Checks for any maintenance to run
     *
     * @return mixed  True || PEAR_Error
     */
    function doMaintenance()
    {
        global $prefs;

        // Kinda hackish way of indicating what tasks need to run, until
        // a more general mechanism is available.
        $needed_tasks = array('upgradeprefs', 'upgradelists');

        $successful = array();
        $existing = @unserialize($GLOBALS['prefs']->getValue('turba_maintenance_tasks'));
        if (empty($existing)) {
            $existing = array();
        }
        foreach ($needed_tasks as $taskname) {
            if (array_search($taskname, $existing) === false) {
                include dirname(__FILE__) . '/Maintenance/Task/' . basename($taskname) . '.php';
                $class = 'Maintenance_Task_Turba_' . $taskname;
                if (class_exists($class)) {
                    $task = &new $class();
                    $result = $task->doMaintenance();
                    if (is_a($result, 'PEAR_Error')) {
                        // Mark any successful taks before failing.
                        $prefs->setValue('turba_maintenance_tasks', serialize(array_merge($existing, $successful)));
                        return $result;
                    } elseif ($result) {
                        $successful[] = $taskname;
                    }
                } else {
                    $prefs->setValue('turba_maintenance_tasks', serialize(array_merge($existing, $successful)));
                    return PEAR::raiseError(sprintf(_("Unable to load the definition of %s."), $class));
                }
            }
        }
        $prefs->setValue('turba_maintenance_tasks', serialize(array_merge($existing, $successful)));
        return true;
    }

}

<?php
/**
 * String that can't be a valid folder name used to mark blacklisted email as
 * deleted.
 */
define('INGO_BLACKLIST_MARKER', '++DELETE++');

/**
 * Ingo base class.
 *
 * $Horde: ingo/lib/Ingo.php,v 1.69.6.23 2008-12-15 02:33:08 chuck Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @package Ingo
 */
class Ingo {

    /**
     * Generates a folder widget.
     * If an application is available that provides a folderlist method
     * then a &lt;select&gt; input is created else a simple text field
     * is returned.
     *
     * @param string $value    The current value for the field.
     * @param string $form     The form name for the newFolderName() call.
     * @param string $tagname  The label for the select tag.
     * @param string $onchange Javascript code to execute onchange.
     *
     * @return string  The HTML to render the field.
     */
    function flistSelect($value = null, $form = null, $tagname = 'actionvalue',
                         $onchange = null)
    {
        global $conf, $registry;

        if (!empty($conf['rules']['usefolderapi']) &&
            $registry->hasMethod('mail/folderlist')) {
            $mailboxes = $registry->call('mail/folderlist');
            if (!is_a($mailboxes, 'PEAR_Error')) {
                $createfolder = $registry->hasMethod('mail/createFolder');

                $text = '<select id="' . $tagname . '" name="' . $tagname . '"';
                if ($createfolder || $onchange) {
                    $text .= ' onchange="';
                    if ($onchange) {
                        $text .= $onchange . ';';
                    }
                    if ($createfolder) {
                        $text .= 'newFolderName(\'' . $form . '\', \'' .
                            $tagname . '\');';
                    }
                    $text .= '"';
                }
                $text .= ">\n";
                $text .= '<option value="">' . _("Select target folder:") . "</option>\n";

                if ($registry->hasMethod('mail/createFolder')) {
                    $text .= '<option value="">' . _("Create new folder") . "</option>\n";
                }

                require_once 'Horde/Text.php';

                foreach ($mailboxes as $mbox) {
                    $sel = ($mbox['val'] && ($mbox['val'] === $value)) ? ' selected="selected"' : '';
                    $disabled = empty($mbox['val']) ? ' disabled="disabled"' : '';
                    $val = htmlspecialchars($mbox['val']);
                    $label = $mbox['abbrev'];
                    $text .= sprintf('<option%s value="%s"%s>%s</option>%s',
                                     $disabled, $val, $sel,
                                     Text::htmlSpaces($label), "\n");
                }

                $text .= '</select>';
                return $text;
            }
        }

        return '<input id="' . $tagname . '" name="' . $tagname . '" size="40" value="' . $value . '" />';
    }

    /**
     * Creates a new IMAP folder via an api call.
     *
     * @param string $folder  The name of the folder to create.
     *
     * @return boolean  True on success, false if not created, PEAR_Error on
     *                  failure.
     */
    function createFolder($folder)
    {
        global $registry;

        if ($registry->hasMethod('mail/createFolder')) {
             return $registry->call('mail/createFolder', array('folder' => String::convertCharset($folder, NLS::getCharset(), 'UTF7-IMAP')));
        }

        return false;
    }

    /**
     * Returns the user whose rules are currently being edited.
     *
     * @param boolean $full  Always return the full user name with realm?
     *
     * @return string  The current user.
     */
    function getUser($full = true)
    {
        if (empty($GLOBALS['ingo_shares'])) {
            $user = ($full ||
                     (isset($_SESSION['ingo']['backend']['hordeauth']) &&
                      $_SESSION['ingo']['backend']['hordeauth'] === 'full')) ?
                Auth::getAuth() :
                Auth::getBareAuth();
        } else {
            list(, $user) = explode(':', $_SESSION['ingo']['current_share'], 2);
        }
        return $user;
    }

    /**
     * Returns the domain name, if any of the user whose rules are currently
     * being edited.
     *
     * @return string  The current user's domain name.
     */
    function getDomain()
    {
        $user = Ingo::getUser(true);
        $pos = strpos($user, '@');
        if ($pos !== false) {
            return substr($user, $pos + 1);
        }

        return false;
    }

    /**
     * Connects to the backend and uploads the script and sets it active.
     *
     * @param string $script       The script to set active.
     * @param boolean $deactivate  If true, notification will identify the
     *                             script as deactivated instead of activated.
     *
     * @return boolean  True on success, false on failure.
     */
    function activateScript($script, $deactivate = false)
    {
        global $notification;

        $driver = Ingo::getDriver();
        $res = $driver->setScriptActive($script);
        if (is_a($res, 'PEAR_Error')) {
            $msg = ($deactivate)
              ? _("There was an error deactivating the script.")
              : _("There was an error activating the script.");
            $notification->push($msg . ' ' . _("The driver said: ") . $res->getMessage(), 'horde.error');
            return false;
        } elseif ($res === true) {
            $msg = ($deactivate)
              ? _("Script successfully deactivated.")
              : _("Script successfully activated.");
            $notification->push($msg, 'horde.success');
            return true;
        }

        return false;
    }

    /**
     * Connects to the backend and returns the currently active script.
     *
     * @return string  The currently active script.
     */
    function getScript()
    {
        $driver = Ingo::getDriver();
        return $driver->getScript();
    }

    /**
     * Does all the work in updating the script on the server.
     */
    function updateScript()
    {
        global $notification;

        if ($_SESSION['ingo']['script_generate']) {
            $ingo_script = Ingo::loadIngoScript();
            if (!$ingo_script) {
                $notification->push(_("Script not updated."), 'horde.error');
            } else {
                /* Generate and activate the script. */
                $script = $ingo_script->generate();
                Ingo::activateScript($script);
            }
        }
    }

    /**
     * Determine the backend to use.
     *
     * This decision is based on the global 'SERVER_NAME' and 'HTTP_HOST'
     * server variables and the contents of the 'preferred' either field
     * in the backend's definition.  The 'preferred' field may take a
     * single value or an array of multiple values.
     *
     * @return array  The backend entry.
     *                Calls Horde::fatal() on error.
     */
    function getBackend()
    {
        include INGO_BASE . '/config/backends.php';
        if (!isset($backends) || !is_array($backends)) {
            Horde::fatal(PEAR::raiseError(_("No backends configured in backends.php")), __FILE__, __LINE__);
        }

        $backend = null;
        foreach ($backends as $name => $temp) {
            if (!isset($backend)) {
                $backend = $name;
            } elseif (!empty($temp['preferred'])) {
                if (is_array($temp['preferred'])) {
                    foreach ($temp['preferred'] as $val) {
                        if (($val == $_SERVER['SERVER_NAME']) ||
                            ($val == $_SERVER['HTTP_HOST'])) {
                            $backend = $name;
                        }
                    }
                } elseif (($temp['preferred'] == $_SERVER['SERVER_NAME']) ||
                          ($temp['preferred'] == $_SERVER['HTTP_HOST'])) {
                    $backend = $name;
                }
            }
        }

        /* Check for valid backend configuration. */
        if (!isset($backend)) {
            Horde::fatal(PEAR::raiseError(_("No backend configured for this host")), __FILE__, __LINE__);
        }

        $backends[$backend]['id'] = $name;
        $backend = $backends[$backend];

        if (empty($backend['script'])) {
            Horde::fatal(PEAR::raiseError(sprintf(_("No \"%s\" element found in backend configuration."), 'script')), __FILE__, __LINE__);
        } elseif (empty($backend['driver'])) {
            Horde::fatal(PEAR::raiseError(sprintf(_("No \"%s\" element found in backend configuration."), 'driver')), __FILE__, __LINE__);
        }

        /* Make sure the 'params' entry exists. */
        if (!isset($backend['params'])) {
            $backend['params'] = array();
        }

        return $backend;
    }

    /**
     * Loads a Ingo_Script:: backend and checks for errors.
     *
     * @return Ingo_Script  Script object on success, PEAR_Error on failure.
     */
    function loadIngoScript()
    {
        global $notification;

        require_once INGO_BASE . '/lib/Script.php';
        $ingo_script = Ingo_Script::factory($_SESSION['ingo']['backend']['script'],
                                            isset($_SESSION['ingo']['backend']['scriptparams']) ? $_SESSION['ingo']['backend']['scriptparams'] : array());
        if (is_a($ingo_script, 'PEAR_Error')) {
            Horde::fatal($ingo_script, __FILE__, __LINE__);
        }

        return $ingo_script;
    }

    /**
     * Returns an instance of the configured driver.
     *
     * @return Ingo_Driver  The configured driver.
     */
    function getDriver()
    {
        $params = $_SESSION['ingo']['backend']['params'];

        // Set authentication parameters.
        if (!empty($_SESSION['ingo']['backend']['hordeauth'])) {
            $params['username'] = ($_SESSION['ingo']['backend']['hordeauth'] === 'full')
                        ? Auth::getAuth() : Auth::getBareAuth();
            $params['password'] = Auth::getCredential('password');
        } elseif (isset($_SESSION['ingo']['backend']['params']['username']) &&
                  isset($_SESSION['ingo']['backend']['params']['password'])) {
            $params['username'] = $_SESSION['ingo']['backend']['params']['username'];
            $params['password'] = $_SESSION['ingo']['backend']['params']['password'];
        } else {
            $params['username'] = Auth::getBareAuth();
            $params['password'] = Auth::getCredential('password');
        }

        require_once INGO_BASE . '/lib/Driver.php';
        return Ingo_Driver::factory($_SESSION['ingo']['backend']['driver'], $params);
    }

    /**
     * Returns all rulesets a user has access to, according to several
     * parameters/permission levels.
     *
     * @since Ingo 2.1
     *
     * @param boolean $owneronly   Only return rulesets that this user owns?
     *                             Defaults to false.
     * @param integer $permission  The permission to filter rulesets by.
     *
     * @return array  The ruleset list.
     */
    function listRulesets($owneronly = false, $permission = PERMS_SHOW)
    {
        $rulesets = $GLOBALS['ingo_shares']->listShares(Auth::getAuth(), $permission, $owneronly ? Auth::getAuth() : null);
        if (is_a($rulesets, 'PEAR_Error')) {
            Horde::logMessage($rulesets, __FILE__, __LINE__, PEAR_LOG_ERR);
            return array();
        }

        return $rulesets;
    }

    /**
     * Returns the specified permission for the current user.
     *
     * @since Ingo 1.1
     *
     * @param string $permission  A permission, either 'allow_rules' or
     *                            'max_rules'.
     *
     * @return mixed  The value of the specified permission.
     */
    function hasPermission($permission, $mask = null)
    {
        if ($permission == 'shares') {
            if (!isset($GLOBALS['ingo_shares'])) {
                return true;
            }
            static $all_perms;
            if (!isset($all_perms)) {
                $all_perms = $GLOBALS['ingo_shares']->getPermissions($_SESSION['ingo']['current_share'], Auth::getAuth());
            }
            return $all_perms & $mask;
        }

        global $perms;

        if (!$perms->exists('ingo:' . $permission)) {
            return true;
        }

        $allowed = $perms->getPermissions('ingo:' . $permission);
        if (is_array($allowed)) {
            switch ($permission) {
            case 'allow_rules':
                $allowed = (bool)count(array_filter($allowed));
                break;

            case 'max_rules':
                $allowed = max($allowed);
                break;
            }
        }

        return $allowed;
    }

    /**
     * Returns whether an address is empty or only contains a "@".
     * Helper function for array_filter().
     *
     * @param string $address  An email address to test.
     *
     * @return boolean  True if the address is not empty.
     */
    function _filterEmptyAddress($address)
    {
        $address = trim($address);
        return !empty($address) && $address != '@';
    }

    /**
     * Build Ingo's list of menu items.
     */
    function getMenu($returnType = 'object')
    {
        require_once 'Horde/Menu.php';

        $menu = new Menu();
        $menu->add(Horde::applicationUrl('filters.php'), _("Filter _Rules"), 'ingo.png', null, null, null, basename($_SERVER['PHP_SELF']) == 'index.php' ? 'current' : null);
        if (!is_a($whitelist_url = $GLOBALS['registry']->link('mail/showWhitelist'), 'PEAR_Error')) {
            $menu->add(Horde::url($whitelist_url), _("_Whitelist"), 'whitelist.png');
        }
        if (!is_a($blacklist_url = $GLOBALS['registry']->link('mail/showBlacklist'), 'PEAR_Error')) {
            $menu->add(Horde::url($blacklist_url), _("_Blacklist"), 'blacklist.png');
        }
        if (in_array(INGO_STORAGE_ACTION_VACATION, $_SESSION['ingo']['script_categories'])) {
            $menu->add(Horde::applicationUrl('vacation.php'), _("_Vacation"), 'vacation.png');
        }
        if (in_array(INGO_STORAGE_ACTION_FORWARD, $_SESSION['ingo']['script_categories'])) {
            $menu->add(Horde::applicationUrl('forward.php'), _("_Forward"), 'forward.png');
        }
        if (in_array(INGO_STORAGE_ACTION_SPAM, $_SESSION['ingo']['script_categories'])) {
            $menu->add(Horde::applicationUrl('spam.php'), _("S_pam"), 'spam.png');
        }
        if ($_SESSION['ingo']['script_generate'] &&
            (!$GLOBALS['prefs']->isLocked('auto_update') ||
             !$GLOBALS['prefs']->getValue('auto_update'))) {
            $menu->add(Horde::applicationUrl('script.php'), _("_Script"), 'script.png');
        }
        if (!empty($GLOBALS['ingo_shares']) && empty($GLOBALS['conf']['share']['no_sharing'])) {
            $menu->add('#', _("_Permissions"), 'perms.png', $GLOBALS['registry']->getImageDir('horde'), '', 'popup(\'' . Util::addParameter(Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/shares/edit.php', true), array('app' => 'ingo', 'share' => htmlspecialchars($_SESSION['ingo']['backend']['id'] . ':' . Auth::getAuth())), null, false) . '\');return false;');
        }

        if ($returnType == 'object') {
            return $menu;
        } else {
            return $menu->render();
        }
    }

}

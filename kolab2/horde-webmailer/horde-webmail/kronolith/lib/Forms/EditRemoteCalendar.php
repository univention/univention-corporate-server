<?php
/**
 * Horde_Form for editing remote calendars.
 *
 * $Horde: kronolith/lib/Forms/EditRemoteCalendar.php,v 1.1.2.2 2009-11-25 10:36:52 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Kronolith
 */

/** Variables */
require_once 'Horde/Variables.php';

/** Horde_Form */
require_once 'Horde/Form.php';

/** Horde_Form_Renderer */
require_once 'Horde/Form/Renderer.php';

/**
 * The Kronolith_EditRemoteCalendarForm class provides the form for
 * editing a remote calendar.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_EditRemoteCalendarForm extends Horde_Form {

    function Kronolith_EditRemoteCalendarForm(&$vars, $remote_calendar)
    {
        parent::Horde_Form($vars, sprintf(_("Edit %s"), $remote_calendar['name']));

        $this->addHidden('', 'url', 'text', true);
        $this->addVariable(_("Name"), 'name', 'text', true);
        $v = &$this->addVariable(_("URL"), 'new_url', 'text', true);
        $v->setDefault($vars->get('url'));
        $this->addVariable(_("Username"), 'username', 'text', false);
        $this->addVariable(_("Password"), 'password', 'password', false);

        $this->setButtons(array(_("Save")));
    }

    function execute()
    {
        $name = trim($this->_vars->get('name'));
        $url = trim($this->_vars->get('url'));
        $new_url = trim($this->_vars->get('new_url'));
        $username = trim($this->_vars->get('username'));
        $password = trim($this->_vars->get('password'));

        if (!(strlen($name) && strlen($url))) {
            return false;
        }

        if (strlen($username) || strlen($password)) {
            $key = Auth::getCredential('password');
            if ($key) {
                require_once 'Horde/Secret.php';
                $username = base64_encode(Secret::write($key, $username));
                $password = base64_encode(Secret::write($key, $password));
            }
        }

        $remote_calendars = unserialize($GLOBALS['prefs']->getValue('remote_cals'));
        foreach ($remote_calendars as $key => $calendar) {
            if ($calendar['url'] == $url) {
                $remote_calendars[$key]['name'] = $name;
                $remote_calendars[$key]['url'] = $new_url;
                $remote_calendars[$key]['user'] = $username;
                $remote_calendars[$key]['password'] = $password;
                break;
            }
        }

        $GLOBALS['prefs']->setValue('remote_cals', serialize($remote_calendars));
        return true;
    }

}

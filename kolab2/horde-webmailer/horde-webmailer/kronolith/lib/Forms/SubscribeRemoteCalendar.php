<?php
/**
 * Horde_Form for subscribing to remote calendars.
 *
 * $Horde: kronolith/lib/Forms/SubscribeRemoteCalendar.php,v 1.1.2.1 2007-12-20 14:12:36 jan Exp $
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
 * The Kronolith_SubscribeRemoteCalendarForm class provides the form
 * for subscribing to remote calendars
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_SubscribeRemoteCalendarForm extends Horde_Form {

    function Kronolith_SubscribeRemoteCalendarForm(&$vars)
    {
        parent::Horde_Form($vars, _("Subscribe to a Remote Calendar"));

        $this->addVariable(_("Name"), 'name', 'text', true);
        $this->addVariable(_("URL"), 'url', 'text', true);
        $this->addVariable(_("Username"), 'username', 'text', false);
        $this->addVariable(_("Password"), 'password', 'password', false);

        $this->setButtons(array(_("Subscribe")));
    }

    function execute()
    {
        $name = trim($this->_vars->get('name'));
        $url = trim($this->_vars->get('url'));
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
        $remote_calendars[] = array(
            'name' => $name,
            'url' => $url,
            'user' => $username,
            'password' => $password,
        );

        $GLOBALS['prefs']->setValue('remote_cals', serialize($remote_calendars));
        return true;
    }

}

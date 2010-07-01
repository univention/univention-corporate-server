<?php
/**
 * Horde_Form for unsubscribing from remote calendars.
 *
 * $Horde: kronolith/lib/Forms/UnsubscribeRemoteCalendar.php,v 1.1.2.1 2007-12-20 14:12:36 jan Exp $
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
 * The Kronolith_UnsubscribeRemoteCalendarForm class provides the form for
 * deleting a calendar.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_UnsubscribeRemoteCalendarForm extends Horde_Form {

    function Kronolith_UnsubscribeRemoteCalendarForm(&$vars, $calendar)
    {
        parent::Horde_Form($vars, sprintf(_("Unsubscribe from %s"), $calendar['name']));

        $this->addHidden('', 'url', 'text', true);
        $this->addVariable(sprintf(_("Really unsubscribe from the calendar \"%s\" (%s)?"), $calendar['name'], $calendar['url']), 'desc', 'description', false);

        $this->setButtons(array(_("Unsubscribe"), _("Cancel")));
    }

    function execute()
    {
        // If cancel was clicked, return false.
        if ($this->_vars->get('submitbutton') == _("Cancel")) {
            return false;
        }

        $url = trim($this->_vars->get('url'));
        if (!strlen($url)) {
            return false;
        }

        $remote_calendars = unserialize($GLOBALS['prefs']->getValue('remote_cals'));
        foreach ($remote_calendars as $key => $calendar) {
            if ($calendar['url'] == $url) {
                unset($remote_calendars[$key]);
                break;
            }
        }

        $GLOBALS['prefs']->setValue('remote_cals', serialize($remote_calendars));
        return true;
    }

}

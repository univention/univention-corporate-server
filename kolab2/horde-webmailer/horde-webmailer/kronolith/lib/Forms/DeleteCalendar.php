<?php
/**
 * Horde_Form for deleting calendars.
 *
 * $Horde: kronolith/lib/Forms/DeleteCalendar.php,v 1.3.2.1 2007-12-20 14:12:36 jan Exp $
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
 * The Kronolith_DeleteCalendarForm class provides the form for
 * deleting a calendar.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_DeleteCalendarForm extends Horde_Form {

    /**
     * Calendar being deleted
     */
    var $_calendar;

    function Kronolith_DeleteCalendarForm(&$vars, &$calendar)
    {
        $this->_calendar = &$calendar;
        parent::Horde_Form($vars, sprintf(_("Delete %s"), $calendar->get('name')));

        $this->addHidden('', 'c', 'text', true);
        $this->addVariable(sprintf(_("Really delete the calendar \"%s\"? This cannot be undone and all data on this calendar will be permanently removed."), $this->_calendar->get('name')), 'desc', 'description', false);

        $this->setButtons(array(_("Delete"), _("Cancel")));
    }

    function execute()
    {
        // If cancel was clicked, return false.
        if ($this->_vars->get('submitbutton') == _("Cancel")) {
            return false;
        }

        if ($this->_calendar->get('owner') != Auth::getAuth()) {
            return PEAR::raiseError(_("Permission denied"));
        }

        // Delete the calendar.
        $result = $GLOBALS['kronolith_driver']->delete($this->_calendar->getName());
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete \"%s\": %s"), $this->_calendar->get('name'), $result->getMessage()));
        } else {
            // Remove share and all groups/permissions.
            $result = $GLOBALS['kronolith_shares']->removeShare($this->_calendar);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        // Make sure we still own at least one calendar.
        if (count(Kronolith::listCalendars(true)) == 0) {
            // If the default share doesn't exist then create it.
            if (!$GLOBALS['kronolith_shares']->exists(Auth::getAuth())) {
                require_once 'Horde/Identity.php';
                $identity = &Identity::singleton();
                $name = $identity->getValue('fullname');
                if (trim($name) == '') {
                    $name = Auth::removeHook(Auth::getAuth());
                }
                $calendar = &$GLOBALS['kronolith_shares']->newShare(Auth::getAuth());
                if (is_a($calendar, 'PEAR_Error')) {
                    return;
                }
                $calendar->set('name', sprintf(_("%s's Calendar"), $name));
                $GLOBALS['kronolith_shares']->addShare($calendar);
                $GLOBALS['all_calendars'][Auth::getAuth()] = &$calendar;
            }
        }

        return true;
    }

}

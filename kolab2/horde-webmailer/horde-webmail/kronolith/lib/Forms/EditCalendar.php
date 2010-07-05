<?php
/**
 * Horde_Form for editing calendars.
 *
 * $Horde: kronolith/lib/Forms/EditCalendar.php,v 1.1.2.2 2008-11-12 09:17:11 wrobel Exp $
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
 * The Kronolith_EditCalendarForm class provides the form for
 * editing a calendar.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_EditCalendarForm extends Horde_Form {

    /**
     * Calendar being edited
     */
    var $_calendar;

    function Kronolith_EditCalendarForm(&$vars, &$calendar)
    {
        $this->_calendar = &$calendar;
        parent::Horde_Form($vars, sprintf(_("Edit %s"), $calendar->get('name')));

        $this->addHidden('', 'c', 'text', true);
        if ($this->_calendar->get('owner') != Auth::getAuth()) {
            $this->addVariable(_("Name"), 'name', 'text', false, true);
            $this->addVariable(_("Description"), 'description', 'longtext', false, true);
        } else {
            $this->addVariable(_("Name"), 'name', 'text', true);
            $this->addVariable(_("Description"), 'description', 'longtext', false, false, null, array(4, 60));
        }
        if ($this->_calendar->get('owner') == Auth::getAuth()) {
            $this->addVariable(_("Relevance"), 'fbrelevance', 'radio', false, false, null, 
                               array(array(_("owners/administrators"), _("readers"), _("no one")), 
                                     'This calendar is only included into the free/busy data for ...'));
        }

        $this->setButtons(array(_("Save")));
    }

    function activeSyncSegment($devices)
    {
        $this->addHidden('', 'activesync_devices', 'text');
        $this->addVariable('', '', 'spacer');
        $this->addVariable(_("Synchronization options for ActiveSync devices"), '', 'header');
        foreach ($devices as $id => $config) {
            $this->addVariable(sprintf("Device \"%s\"", $id), 'activesync_' . $id, 'radio', false, false, null, 
                           array(array(_("does not synchronize with this calendar"), _("synchronizes with this calendar but ignores alarms"), _("synchronizes with this calendar including alarms"))));
        }
    }

    function execute()
    {
        $this->_calendar->set('desc', $this->_vars->get('description'));

        $original_name = $this->_calendar->get('name');
        if ($this->_calendar->get('owner') == Auth::getAuth()) {
            $new_name = $this->_vars->get('name');
            $this->_calendar->set('name', $new_name);
            $params = array('fbrelevance' => (int) $this->_vars->get('fbrelevance', 0));
        } else {
            $new_name = $original_name;
        }

        if ($this->_vars->get('activesync_devices', '')) {
            $ids = explode('|', $this->_vars->get('activesync_devices', ''));
            foreach ($ids as $id) {
                $sync = (int) $this->_vars->get('activesync_' . $id, 0);
                if ($sync === 0 || $sync === 1 || $sync === 2) {
                    $params['activesync']['FOLDER'][$id]['S'] = $sync;
                }
            }
        }

        $this->_calendar->set('params', serialize($params));

        if ($original_name != $new_name) {
            $result = $GLOBALS['kronolith_driver']->rename($original_name, $new_name);
            if (is_a($result, 'PEAR_Error')) {
                return PEAR::raiseError(sprintf(_("Unable to rename \"%s\": %s"), $original_name, $result->getMessage()));
            }
        }

        $result = $this->_calendar->save();
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to save calendar \"%s\": %s"), $new_name, $result->getMessage()));
        }
        return true;
    }

}

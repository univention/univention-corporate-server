<?php
/**
 * Horde_Form for creating calendars.
 *
 * $Horde: kronolith/lib/Forms/CreateCalendar.php,v 1.2.2.1 2007-12-20 14:12:36 jan Exp $
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
 * The Kronolith_CreateCalendarForm class provides the form for
 * creating a calendar.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_CreateCalendarForm extends Horde_Form {

    function Kronolith_CreateCalendarForm(&$vars)
    {
        parent::Horde_Form($vars, _("Create Calendar"));

        $this->addVariable(_("Name"), 'name', 'text', true);
        $this->addVariable(_("Description"), 'description', 'longtext', false, false, null, array(4, 60));
        $this->addVariable(_("Relevance"), 'fbrelevance', 'radio', false, false, null, 
                           array(array(_("owners/administrators"), _("readers"), _("no one")), 
                                 'This calendar is only included into the free/busy data for ...'));

        $this->setButtons(array(_("Create")));
    }

    function execute()
    {
        // Create new share.
        $calendar = $GLOBALS['kronolith_shares']->newShare(md5(microtime()));
        if (is_a($calendar, 'PEAR_Error')) {
            return $calendar;
        }
        $calendar->set('name', $this->_vars->get('name'));
        $calendar->set('desc', $this->_vars->get('description'));
        $calendar->set('params', serialize(array('fbrelevance' => (int) $this->_vars->get('fbrelevance', 0))));
        return $GLOBALS['kronolith_shares']->addShare($calendar);
    }

}

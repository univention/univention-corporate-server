<?php

require_once dirname(__FILE__) . '/Week.php';

/**
 * The Kronolith_View_WorkWeek:: class provides a shortcut for a week
 * view that is only Monday through Friday.
 *
 * $Horde: kronolith/lib/Views/WorkWeek.php,v 1.3.2.1 2007-12-20 14:12:38 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_View_WorkWeek extends Kronolith_View_Week {

    var $startDay = HORDE_DATE_MONDAY;
    var $endDay = HORDE_DATE_FRIDAY;
    var $_controller = 'workweek.php';

    function getName()
    {
        return 'WorkWeek';
    }

}

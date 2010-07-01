<?php

require_once dirname(__FILE__) . '/week.php';

/**
 * This class represent a work week of free busy information sets.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView/workweek.php,v 1.7.10.8 2009-01-06 15:24:46 jan Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View_workweek extends Kronolith_FreeBusy_View_week {

    var $view = 'workweek';
    var $_days = 5;

}

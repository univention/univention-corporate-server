<?php
/**
 * $Horde: kronolith/attendees.php,v 1.5 2004/05/25 08:34:21 stuart Exp $
 *
 * Copyright 2004 Code Fusion  <http://www.codefusion.co.za/>
 *                Stuart Binge <s.binge@codefusion.co.za>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

$allow_dismiss = true;
$form_handler = Horde::applicationUrl('attendees.php');
require KRONOLITH_BASE . '/attendeeshandler.php';

$title = _('Edit attendees');

Horde::addScriptFile('tooltip.js', 'horde');
require KRONOLITH_TEMPLATES . '/common-header.inc';

require KRONOLITH_BASE . '/attendeescommon.php';

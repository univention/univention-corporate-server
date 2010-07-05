<?php
/**
 * $Horde: nag/search.php,v 1.17.8.7 2009-01-06 15:25:04 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('NAG_BASE', dirname(__FILE__));
require_once NAG_BASE . '/lib/base.php';

$title = _("Search");
$notification->push('document.search.search_pattern.focus()', 'javascript');
Horde::addScriptFile('prototype.js', 'nag', true);
require NAG_TEMPLATES . '/common-header.inc';
require NAG_TEMPLATES . '/menu.inc';
require NAG_TEMPLATES . '/search/search.inc';
require NAG_TEMPLATES . '/panel.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';

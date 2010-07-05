<?php
/**
 * $Horde: horde/services/download/index.php,v 1.9.10.7 2009-01-06 15:26:21 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/core.php';

$registry = &Registry::singleton(HORDE_SESSION_READONLY);

if (!($module = Util::getFormData('module')) ||
    !file_exists($registry->get('fileroot', $module))) {
    Horde::fatal('Do not call this script directly.', __FILE__, __LINE__);
}
include $registry->get('fileroot', $module) . '/view.php';

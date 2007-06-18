<?php
/**
 * $Horde: horde/services/download/index.php,v 1.7 2004/04/20 21:20:07 chuck Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/core.php';

$registry = &Registry::singleton();

if (!($module = Util::getFormData('module')) ||
    !file_exists($registry->getParam('fileroot', $module))) {
    Horde::fatal('Do not call this script directly.', __FILE__, __LINE__);
}
include $registry->getParam('fileroot', $module) . '/view.php';

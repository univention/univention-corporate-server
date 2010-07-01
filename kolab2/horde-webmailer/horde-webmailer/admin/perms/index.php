<?php
/**
 * $Horde: horde/admin/perms/index.php,v 1.10.10.8 2009-01-06 15:22:10 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Jan Schneider <jan@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

$perm_id = Util::getFormData('perm_id');

$title = _("Permissions Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/menu.inc';

require_once 'Horde/Perms/UI.php';
$ui = &new Perms_UI($perms);
$notification->notify();
$ui->renderTree($perm_id);

require HORDE_TEMPLATES . '/common-footer.inc';

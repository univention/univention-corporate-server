<?php
/**
 * $Horde: turba/deletefile.php,v 1.6.2.3 2009-01-06 15:27:38 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';

if ($conf['documents']['type'] == 'none') {
    exit;
}

$source = Util::getPost('source');
if ($source === null || !isset($cfgSources[$source])) {
    $notification->push(_("Not found"), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

$driver = &Turba_Driver::singleton($source);
$contact = $driver->getObject(Util::getPost('key'));
if (is_a($contact, 'PEAR_Error')) {
    $notification->push($contact, 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

if (!$contact->isEditable()) {
    $notification->push(_("Permission denied"), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

$file = Util::getPost('file');
$result = $contact->deleteFile($file);
if (is_a($result, 'PEAR_Error')) {
    $notification->push($result, 'horde.error');
} else {
    $notification->push(sprintf(_("The file \"%s\" has been deleted."), $file), 'horde.success');
}
$url = header('Location: ' . $contact->url('Contact', true));

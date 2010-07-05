<?php
/**
 * $Horde: horde/services/portal/mobile.php,v 2.15.10.8 2009-01-06 15:27:33 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Identity.php';
require_once 'Horde/Mobile.php';

if (!Auth::getAuth()) {
    header('Location: ' . Util::addParameter(Horde::applicationUrl('login.php', true),
                                             'url', Horde::selfUrl(), false));
    exit;
}

$identity = &Identity::singleton();
$fullname = $identity->getValue('fullname');
if (empty($fullname)) {
    $fullname = Auth::getAuth();
}

$m = &new Horde_Mobile(_("Welcome"));
$m->add(new Horde_Mobile_text(sprintf(_("Welcome, %s"), $fullname)));

// Messy way of linking to active apps that support mobile devices. Should be
// made more elegant at some point.
if (in_array('mimp', $registry->listApps())) {
    $m->add(new Horde_Mobile_link($registry->get('name', 'mimp'),
                                  Horde::url($registry->get('webroot', 'mimp') . '/'),
                                  $registry->get('name', 'mimp')));
}

$m->display();

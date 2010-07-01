<?php
/**
 * Script to set the new language.
 *
 * $Horde: horde/services/language.php,v 1.5.12.8 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Marko Djukic <marko@oblo.com>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';

/* Set the language. */
$_SESSION['horde_language'] = NLS::select();
$prefs->setValue('language', $_SESSION['horde_language']);

/* Update apps language */
foreach ($registry->listAPIs() as $api) {
    if ($registry->hasMethod($api . '/changeLanguage')) {
        $registry->call($api . '/changeLanguage');
    }
}

/* Redirect to the url or login page if none given. */
$url = Util::getFormData('url');
if (empty($url)) {
    $url = Horde::applicationUrl('index.php', true);
}
header('Location: ' . $url);

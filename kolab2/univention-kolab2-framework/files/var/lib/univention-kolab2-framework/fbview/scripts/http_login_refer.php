<?php
/**
 * $Horde: horde/scripts/http_login_refer.php,v 1.3 2004/01/01 15:16:54 jan Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

require_once '../lib/base.php';

$auth = &Auth::singleton($conf['auth']['driver']);

// Check for HTTP auth.
if (empty($_SERVER['PHP_AUTH_USER']) ||
    empty($_SERVER['PHP_AUTH_PW']) ||
    !$auth->authenticate($_SERVER['PHP_AUTH_USER'],
                         array('password' => $_SERVER['PHP_AUTH_PW']))) {

    header('WWW-Authenticate: Basic realm="' . $auth->getParam('realm') . '"');
    header('HTTP/1.0 401 Unauthorized');
    exit('Forbidden');
}

if ($url = Util::getFormData('url')) {
    header('Location: ' . $url);
} else {
    header('Location: ' . Horde::applicationUrl('login.php'));
}

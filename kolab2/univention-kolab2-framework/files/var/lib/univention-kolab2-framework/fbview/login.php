<?php
/**
 * $Horde: horde/login.php,v 2.157 2004/04/08 21:19:20 chuck Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Secret.php';

/* Initialize the Auth credentials key. */
Secret::setKey('auth');

/* Get an Auth object. */
$auth = &Auth::singleton($conf['auth']['driver']);
if (is_a($auth, 'PEAR_Error')) {
    Horde::fatal($auth, __FILE__, __LINE__);
}

/* Get parameters. */
$logout_reason = $auth->getLogoutReason();
$url_param = Util::getFormData('url');

if ($logout_reason) {
    $login_screen = $auth->_getLoginScreen();
    if (Util::removeParameter($login_screen, array('url', 'nocache')) !=
        Util::removeParameter(Horde::url(Horde::selfUrl(), true), array('url', 'nocache'))) {
        $url = Auth::addLogoutParameters($login_screen);
        if ($url_param) {
            $url = Util::addParameter($login_screen, 'url', $url_param);
        }
        header('Location: ' . $url);
        exit;
    }

    $language = isset($prefs) ? $prefs->getValue('language') : NLS::select();

    $entry = sprintf('User %s [%s] logged out of Horde',
                     Auth::getAuth(), $_SERVER['REMOTE_ADDR']);
    Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_INFO);
    Auth::clearAuth();
    session_destroy();

    /* If logout has a set initial page, redirect to that. Check that
     * it is not a looping redirect. */
    if (isset($registry->applications['logout']['initial_page']) &&
        ($registry->applications['logout']['initial_page'] != ('login.php?' . AUTH_REASON_PARAM . '=' . AUTH_REASON_LOGOUT))) {
        header('Location: ' . Horde::applicationUrl($registry->applications['logout']['initial_page']));
        exit;
    }

    Horde::setupSessionHandler();
    @session_start();

    NLS::setLang($language);

    /* Hook to preselect the correct language in the widget. */
    $_GET['new_lang'] = $language;
}

if (isset($_POST['horde_user']) && isset($_POST['horde_pass'])) {

    /* Destroy any existing session on login and make sure to use a
     * new session ID, to avoid session fixation issues. */
    Horde::getCleanSession();
    if ($auth->authenticate(Util::getPost('horde_user'),
                            array('password' => Util::getPost('horde_pass')))) {
        $entry = sprintf('Login success for %s [%s] to Horde',
                         Auth::getAuth(), $_SERVER['REMOTE_ADDR']);
        Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_INFO);

        if ($url_param) {
            $url = Horde::url(Util::removeParameter($url_param, session_name()), true);
            $horde_url = Horde::applicationUrl($registry->getParam('webroot', 'horde') . '/index.php', true);
            $horde_url = Util::addParameter($horde_url, 'url', $url);
        } else {
            $horde_url = Horde::applicationUrl('index.php', true);
        }

        $horde_url = Util::addParameter($horde_url, 'frameset', Util::getFormData('frameset') ? 1 : 0);
	$prefs->setValue('language', $_POST['new_lang']);
        header('Location: ' . $horde_url);
        exit;
    } else {
        $entry = sprintf('FAILED LOGIN for %s [%s] to Horde',
                         Util::getFormData('horde_user'), $_SERVER['REMOTE_ADDR']);
        Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_ERR);
        if ($conf['menu']['always'] && !Util::getFormData('framed')) {
            $main_page = Util::addParameter(Horde::selfUrl(), 'framed', $auth->getLogoutReasonString());
            if ($browser->hasQuirk('scrollbar_in_way')) {
                $scrollbar = 'yes';
            } else {
                $scrollbar = 'auto';
            }
            require HORDE_TEMPLATES . '/index/frames_index.inc';
            exit;
        } 
    }
}

if (Auth::getAuth()) {
    if ($browser->isMobile()) {
        $url = 'services/portal/mobile.php';
    } else {
        $url = 'services/portal/index.php';
    }
    require HORDE_BASE . '/' . $url;
    exit;
}

/* Try transparent authentication. */
if (Auth::isAuthenticated()) {
    require HORDE_BASE . '/index.php';
    exit;
}

$login_screen = $auth->_getLoginScreen();
if (Util::removeParameter($login_screen, array('url', 'nocache')) !=
    Util::removeParameter(Horde::url(Horde::selfUrl(), true), array('url', 'nocache'))) {
    if ($url_param) {
        $login_screen = Util::addParameter($login_screen, 'url', $url_param);
    }
    $login_screen = Util::addParameter($login_screen, 'frameset', Util::getFormData('frameset'));
    header('Location: ' . $login_screen);
    exit;
}

if ($browser->isMobile()) {
    require_once 'Horde/Mobile.php';
    require HORDE_TEMPLATES . '/login/mobile.inc';
    exit;
}

/* Build the <select> widget containing the available languages. */
if (!$prefs->isLocked('language')) {
    $_SESSION['horde_language'] = NLS::select();
    $langs = '<select name="new_lang" onchange="selectLang()">';
    foreach ($nls['languages'] as $key => $val) {
        $sel = ($key == $_SESSION['horde_language']) ? ' selected="selected"' : '';
        $langs .= "<option value=\"$key\"$sel>$val</option>";
    }
    $langs .= '</select>';
}

$title = _("Log in");
$notification->push('setFocus()', 'javascript');
if ($logout_reason && $conf['menu']['always']) {
    $notification->push('if (window.parent.frames.horde_menu) window.parent.frames.horde_menu.location.reload();', 'javascript');
}

$reason = $auth->getLogoutReasonString();

/* Add some javascript. */
Horde::addScriptFile('enter_key_trap.js', 'horde');

require HORDE_TEMPLATES . '/common-header.inc';
$notification->notify(array('listeners' => 'status'));
require HORDE_TEMPLATES . '/login/login.inc';
require HORDE_TEMPLATES . '/common-footer.inc';

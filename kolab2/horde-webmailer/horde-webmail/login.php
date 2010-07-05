<?php
/**
 * $Horde: horde/login.php,v 2.175.2.17 2009-01-06 15:13:50 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

/* Add anchor to outgoing URL. */
function _addAnchor($url, $type)
{
    switch ($type) {
    case 'param':
        if (!empty($GLOBALS['url_anchor'])) {
            $url .= '#' . $GLOBALS['url_anchor'];
        }
        break;

    case 'url':
        $anchor = Util::getFormData('anchor_string');
        if (!empty($anchor)) {
            $url .= '#' . $anchor;
        } else {
            return _addAnchor($url, 'param');
        }
        break;
    }

    return $url;
}

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/base.php';
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
$ie_version = Util::getFormData('ie_version');

/* Get URL/Anchor strings now. */
$url_anchor = null;
$url_in = $url_form = Util::getFormData('url');
if (($pos = strrpos($url_in, '#')) !== false) {
    $url_anchor = substr($url_in, $pos + 1);
    $url_in = substr($url_in, 0, $pos);
}

if ($logout_reason) {
    if (Auth::getAuth()) {
        $result = Horde::checkRequestToken('horde.logout', Util::getFormData('horde_logout_token'));
        if (is_a($result, 'PEAR_Error')) {
            exit($result->getMessage());
        }
    }

    $login_screen = $auth->getLoginScreen();
    if (Util::getFormData('nosidebar') &&
        isset($GLOBALS['notification'])) {
        $url = Auth::addLogoutParameters($login_screen);
        if (!empty($url_in)) {
            $url = Util::addParameter($url, 'url', _addAnchor($url_in, 'param'));
        }
        $notification->push('window.parent.location.href = \'' . _addAnchor($url, 'url') . '\';', 'javascript');
        echo '<html><body>' . $GLOBALS['notification']->notify(array('listeners' => array('javascript'))) . '</body></html>';
        exit;
    }

    if (Util::removeParameter($login_screen, array('url', 'nocache')) !=
        Util::removeParameter(Horde::selfUrl(false, false, true), array('url', 'nocache'))) {
        $url = Auth::addLogoutParameters($login_screen);
        if ($url_in) {
            $url = Util::addParameter($url, 'url', _addAnchor($url_in, 'param'));
        }
        header('Location: ' . _addAnchor($url, 'url'));
        exit;
    }

    $language = isset($prefs) ? $prefs->getValue('language') : NLS::select();

    $entry = sprintf('User %s [%s] logged out of Horde',
                     Auth::getAuth(), $_SERVER['REMOTE_ADDR']);
    Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_NOTICE);
    Auth::clearAuth();
    @session_destroy();

    /* Redirect the user on logout if redirection is enabled. */
    if (!empty($conf['auth']['redirect_on_logout'])) {
        $logout_url = $conf['auth']['redirect_on_logout'];
        if (!isset($_COOKIE[session_name()])) {
            $logout_url = Util::addParameter($logout_url, session_name(), session_id());
        }
        header('Location: ' . _addAnchor($logout_url, 'url'));
        exit;
    }

    Horde::setupSessionHandler();
    @session_start();

    NLS::setLang($language);

    /* Hook to preselect the correct language in the widget. */
    $_GET['new_lang'] = $language;

    if ($conf['menu']['always']) {
        $main_page = Util::addParameter(Horde::selfUrl(), 'reason', $auth->getLogoutReasonString());
        if ($browser->hasQuirk('scrollbar_in_way')) {
            $scrollbar = 'yes';
        } else {
            $scrollbar = 'auto';
        }
        require HORDE_TEMPLATES . '/index/frames_index.inc';
        exit;
    }
}

if (isset($_POST['horde_user']) && isset($_POST['horde_pass'])) {
    /* Destroy any existing session on login and make sure to use a
     * new session ID, to avoid session fixation issues. */
    Horde::getCleanSession();
    if ($auth->authenticate(Util::getPost('horde_user'),
                            array('password' => Util::getPost('horde_pass')))) {
        $entry = sprintf('Login success for %s [%s] to Horde',
                         Auth::getAuth(), $_SERVER['REMOTE_ADDR']);
        Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_NOTICE);

        if ($ie_version) {
            $browser->setIEVersion($ie_version);
        }

        if (!empty($url_in)) {
            $url = Horde::url(Util::removeParameter($url_in, session_name()), true);
            $horde_url = $registry->get('webroot', 'horde') . '/index.php';
            $horde_url = Util::addParameter($horde_url, 'url', _addAnchor($url, 'param'));
        } else {
            $horde_url = Horde::url($registry->get('webroot', 'horde') . '/index.php');
        }

        $url = _addAnchor(Horde::applicationUrl($horde_url, true), 'url');
        if ($browser->isBrowser('msie') &&
            $conf['use_ssl'] == 3 &&
            strlen($url) < 160) {
            header('Refresh: 0; URL=' . $url);
        } else {
            header('Location: ' . $url);
        }
        exit;
    } else {
        $entry = sprintf('FAILED LOGIN for %s [%s] to Horde',
                         Util::getFormData('horde_user'), $_SERVER['REMOTE_ADDR']);
        Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_ERR);
        if ($conf['menu']['always']) {
            $main_page = Util::addParameter(Horde::selfUrl(), 'reason', $auth->getLogoutReasonString());
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

/* Redirect the user if an alternate login page has been specified. */
if (!empty($conf['auth']['alternate_login'])) {
    $url = Auth::addLogoutParameters($conf['auth']['alternate_login']);
    if (!isset($_COOKIE[session_name()])) {
        $url = Util::addParameter($url, session_name(), session_id(), false);
    }
    if (!empty($url_in)) {
        $url = Util::addParameter($url, 'url', _addAnchor($url_in, 'param'), false);
    }
    header('Location: ' . _addAnchor($url, 'url'));
    exit;
}

$login_screen = $auth->_getLoginScreen();
if (Util::removeParameter($login_screen, array('url', 'nocache')) !=
    Horde::selfUrl(false, false, true)) {
    if (!empty($url_in)) {
        $login_screen = Util::addParameter($login_screen, 'url', _addAnchor($url_in, 'param'), false);
    }
    if ($ie_version) {
        $login_screen = Util::addParameter($login_screen, 'ie_version', $ie_version, false);
    }
    header('Location: ' . _addAnchor($login_screen, 'url'));
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
    $langs = '<select id="new_lang" name="new_lang" onchange="selectLang()">';
    foreach ($nls['languages'] as $key => $val) {
        $sel = ($key == $_SESSION['horde_language']) ? ' selected="selected"' : '';
        $langs .= "<option value=\"$key\"$sel>$val</option>";
    }
    $langs .= '</select>';
}

$title = _("Log in");
$notification->push('setFocus()', 'javascript');
if ($logout_reason && $conf['menu']['always']) {
    $notification->push('if (window.parent.frames.horde_menu) window.parent.frames.horde_menu.location.href = \'' . Horde::applicationUrl('services/portal/sidebar.php') . '\';', 'javascript');
}

if ($reason = $auth->getLogoutReasonString()) {
    $notification->push(str_replace('<br />', ' ', $reason), 'horde.message');
}

/* Do we need to do IE version detection? */
if (($browser->getBrowser() == 'msie') && ($browser->getMajor() >= 5)) {
    $ie_clientcaps = true;
}

require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/login/login.inc';
require HORDE_TEMPLATES . '/common-footer.inc';

<?php
/**
 * $Horde: imp/redirect.php,v 1.116.2.28 2009-01-06 15:24:02 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

function _framesetUrl($url)
{
    if (!$GLOBALS['noframeset'] && Util::getFormData('load_frameset')) {
        $full_url = Horde::applicationUrl($GLOBALS['registry']->get('webroot', 'horde') . '/index.php', true);
        $url = Util::addParameter($full_url, 'url', _addAnchor($url, 'param'), false);
    }
    return $url;
}

function _newSessionUrl($actionID, $isLogin, $view)
{
    $url = '';
    $addActionID = true;

    $apps = $GLOBALS['registry']->listApps(null, true);
    $default_view = ($GLOBALS['browser']->isMobile() && isset($apps['mimp'])) ? 'mimp' : 'imp';

    if ($GLOBALS['url_in']) {
        $url = Horde::url(Util::removeParameter($GLOBALS['url_in'], session_name()), true);
    } elseif ($view != $default_view || $view != 'imp') {
        $GLOBALS['noframeset'] = true;
        return Horde::url($GLOBALS['registry']->get('webroot', $view) . '/', true);
    } elseif (Auth::getProvider() == 'imp') {
        $url = Horde::applicationUrl($GLOBALS['registry']->get('webroot', 'horde') . '/', true);
        /* Force the initial page to IMP if we're logging in to compose a
         * message. */
        if ($actionID == 'login_compose') {
            $url = Util::addParameter($url, 'url', _addAnchor(IMP_Session::getInitialUrl('login_compose', false), 'param'));
            $addActionID = false;
        }
    } else {
        $url = IMP_Session::getInitialUrl($actionID, false);
        if ($isLogin) {
            /* Don't show popup window in initial page. */
            $url = Util::addParameter($url, 'no_newmail_popup', 1, false);
        }
    }

    if ($addActionID && $actionID) {
        /* Preserve the actionID. */
        $url = Util::addParameter($url, 'actionID', $actionID, false);
    }

    return $url;
}

function _redirect($url)
{
    IMP::redirect(_addAnchor($url, 'url'));
}

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
$authentication = 'none';
require_once dirname(__FILE__) . '/lib/base.php';
require_once IMP_BASE . '/lib/Session.php';
require_once 'Horde/Maintenance.php';

$actionID = (Util::getFormData('action') == 'compose') ? 'login_compose' : Util::getFormData('actionID');
$autologin = Util::getFormData('autologin');
$imapuser = Util::getPost('imapuser');
$pass = Util::getPost('pass');
if (!empty($autologin)) {
    if (empty($GLOBALS['conf']['server']['change_server'])) {
        $imapuser = Auth::getBareAuth();
        $pass = Auth::getCredential('password');
    } elseif (($credentials = @unserialize($prefs->getValue('credentials'))) &&
              isset($credentials['imp'])) {
        $imapuser = $credentials['imp']['username'];
        $pass = $credentials['imp']['password'];
    }
}
$isLogin = IMP::loginTasksFlag();
$noframeset = false;

/* Get URL/Anchor strings now. */
$url_anchor = null;
$url_in = $url_form = Util::getFormData('url');
if (($pos = strrpos($url_in, '#')) !== false) {
    $url_anchor = substr($url_in, $pos + 1);
    $url_in = substr($url_in, 0, $pos);
}

/* If we are returning from Maintenance processing. */
if (Util::getFormData(MAINTENANCE_DONE_PARAM)) {
    /* Finish up any login tasks we haven't completed yet. */
    IMP_Session::loginTasks();

    _redirect(_framesetUrl(_newSessionUrl($actionID, $isLogin, isset($_SESSION['imp']['default_view']) ? $_SESSION['imp']['default_view'] : 'imp')));
}

/* If we already have a session: */
if (isset($_SESSION['imp']) && is_array($_SESSION['imp'])) {
    /* Make sure that if a username was specified, it is the current
     * username. */
    if (($imapuser !== null && ($imapuser != $_SESSION['imp']['user'])) ||
        ($pass !== null && ($pass != Secret::read(Secret::getKey('imp'), $_SESSION['imp']['pass'])))) {

        /* Disable the old session. */
        unset($_SESSION['imp']);
        _redirect(Auth::addLogoutParameters(IMP::logoutUrl(), AUTH_REASON_FAILED));
    }

    /* Finish up any login tasks we haven't completed yet. */
    IMP_Session::loginTasks();

    $url = $url_in;
    if (empty($url_in)) {
        $url = IMP_Session::getInitialUrl($actionID, false);
    } elseif (!empty($actionID)) {
        $url = Util::addParameter($url_in, 'actionID', $actionID, false);
    }

    /* Don't show popup window in initial page. */
    if ($isLogin) {
        $url = Util::addParameter($url, 'no_newmail_popup', 1, false);
    }

    _redirect(_framesetUrl($url));
}

/* Create a new session if we're given the proper parameters. */
if (($imapuser !== null) && ($pass !== null)) {
    if (Auth::getProvider() == 'imp') {
        /* Destroy any existing session on login and make sure to use a new
         * session ID, to avoid session fixation issues. */
        Horde::getCleanSession();
    }

    /* Read the required server parameters from the servers.php file. */
    if (is_callable(array('Horde', 'loadConfiguration'))) {
        $result = Horde::loadConfiguration('servers.php', array('servers'));
        if (!is_a($result, 'PEAR_Error')) {
            extract($result);
        }
    } else {
        require IMP_BASE . '/config/servers.php';
    }
    $server_key = Util::getFormData('server_key', IMP::getAutoLoginServer(true));
    if (!empty($servers[$server_key])) {
        $sessArray = $servers[$server_key];
    }

    /* If we're not using hordeauth get parameters altered from the defaults
     * from the form data. */
    if (empty($autologin)) {
        $credentials = $prefs->getValue('credentials');
        foreach (array('server', 'port', 'protocol', 'smtphost', 'smtpport') as $val) {
            $data = Util::getFormData($val);
            if (!empty($data)) {
                $sessArray[$val] = $data;
            }
        }
    } else {
        if (!empty($GLOBALS['conf']['server']['change_server']) &&
            isset($credentials['imp'])) {
            $sessArray = array_merge($sessArray, $credentials['imp']);
        } elseif (!empty($sessArray['hordeauth'])) {
            if (strcasecmp($sessArray['hordeauth'], 'full') == 0) {
                $imapuser = Auth::getAuth();
            }
        } else {
            $entry = sprintf('Invalid server key "%s" from client [%s]', $server_key, $_SERVER['REMOTE_ADDR']);
            Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_INFO);
        }
    }

    if (!empty($sessArray) &&
        IMP_Session::createSession($imapuser, $pass, $sessArray['server'], $sessArray)) {
        $ie_version = Util::getFormData('ie_version');
        if ($ie_version) {
            $browser->setIEVersion($ie_version);
        }

        if (($horde_language = Util::getFormData('new_lang'))) {
            $_SESSION['horde_language'] = $horde_language;
        }

        /* If this is a recompose attempt, redirect to the compose page now. */
        if (IMP::recomposeLogin()) {
            // Store the user's message data in their session, so that
            // we can redirect to compose.php. This insures that
            // everything gets loaded with a proper session present,
            // which can affect things like the user's preferences.
            $_SESSION['recompose_formData'] = Util::getPost('recompose');
            header('Location: ' . Util::addParameter(Horde::applicationUrl('compose.php', true), 'actionID', 'recompose', false));
            exit;
        }

        if (!empty($conf['hooks']['postlogin'])) {
            Horde::callHook('_imp_hook_postlogin', array($actionID, $isLogin), 'imp');
        }

        if (empty($conf['user']['select_view'])) {
            $view = empty($conf['user']['force_view']) ? 'imp' : $conf['user']['force_view'];
        } else {
            $view = Util::getFormData('select_view', 'imp');
        }
        setcookie('default_imp_view', $view, time() + 30 * 86400,
                  $conf['cookie']['path'],
                  $conf['cookie']['domain']);
        $_SESSION['imp']['default_view'] = $view;

        IMP_Session::loginTasks();

        _redirect(_framesetUrl(_newSessionUrl($actionID, $isLogin, $view)));
    }

    _redirect(Auth::addLogoutParameters(IMP::logoutUrl()));
}

/* No session, and no login attempt. Just go to the login page. */
require IMP_BASE . '/login.php';

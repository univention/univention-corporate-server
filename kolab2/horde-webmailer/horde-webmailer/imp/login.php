<?php
/**
 * Login screen for IMP.
 *
 * $Horde: imp/login.php,v 2.222.2.27 2009-01-06 15:24:01 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

function _getFormData($val, $recompose_data = null)
{
    static $fd;
    if (!isset($fd)) {
        $fd = @unserialize($recompose_data);
    }

    if (!empty($fd['post'][$val])) {
        return $fd['post'][$val];
    } elseif (!empty($fd['get'][$val])) {
        return $fd['get'][$val];
    } else {
        return '';
    }
}

@define('AUTH_HANDLER', true);
$authentication = 'none';
require_once dirname(__FILE__) . '/lib/base.php';
require_once IMP_BASE . '/lib/Template.php';

/* Get an Auth object. */
$imp_auth = (Auth::getProvider() == 'imp');
$auth = &Auth::singleton($conf['auth']['driver']);
$logout_reason = $auth->getLogoutReason();

$actionID = (Util::getFormData('action') == 'compose') ? 'login_compose' : Util::getFormData('actionID');

$recompose_data = Util::getPost('recompose', Util::nonInputVar('RECOMPOSE') ? serialize(array('get' => $_GET, 'post' => $_POST)) : null);

$url_param = Util::getFormData('url');

// RECOMPOSE: If we somehow get to this page with a valid session, go
// immediately to compose.php. No need to do other validity checks if the
// session already exists.
if (!empty($recompose_data) &&
    Auth::getAuth() &&
    IMP::checkAuthentication(true)) {
    $_SESSION['recompose_formData'] = serialize(array('get' => $_GET, 'post' => $_POST));
    header('Location: ' . Util::addParameter(Horde::applicationUrl('compose.php', true), 'actionID', 'recompose', false));
    exit;
}

/* Handle cases where we already have a session. */
if (!empty($_SESSION['imp']) && is_array($_SESSION['imp'])) {
    if ($logout_reason) {
        /* Log logout requests now. */
        if ($logout_reason == AUTH_REASON_LOGOUT) {
            $entry = IMP::loginLogMessage('logout');
        } else {
            $entry = $_SERVER['REMOTE_ADDR'] . ' ' . $auth->getLogoutReasonString();
        }
        Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_NOTICE);

        $language = (isset($prefs)) ? $prefs->getValue('language') : NLS::select();

        unset($_SESSION['imp']);

        /* Cleanup preferences. */
        if (isset($prefs)) {
            $prefs->cleanup($imp_auth);
        }

        if ($imp_auth) {
            Auth::clearAuth();
            @session_destroy();
            Horde::setupSessionHandler();
            @session_start();
        }

        NLS::setLang($language);

        /* Hook to preselect the correct language in the widget. */
        $_GET['new_lang'] = $language;

        $registry->loadPrefs('horde');
        $registry->loadPrefs();
    } else {
        require_once IMP_BASE . '/lib/Session.php';
        header('Location: ' . IMP_Session::getInitialUrl($actionID, false));
        exit;
    }
}

/* Log session timeouts. */
if ($logout_reason == AUTH_REASON_SESSION) {
    $entry = sprintf('Session timeout for client [%s]', $_SERVER['REMOTE_ADDR']);
    Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_NOTICE);

    /* Make sure everything is really cleared. */
    Auth::clearAuth();
    unset($_SESSION['imp']);
}

/* Redirect the user on logout if redirection is enabled. */
if ($logout_reason == AUTH_REASON_LOGOUT &&
    ($conf['user']['redirect_on_logout'] ||
     !empty($conf['auth']['redirect_on_logout']))) {
    if (!empty($conf['auth']['redirect_on_logout'])) {
        $url = Auth::addLogoutParameters($conf['auth']['redirect_on_logout'], AUTH_REASON_LOGOUT);
    } else {
        $url = Auth::addLogoutParameters($conf['user']['redirect_on_logout'], AUTH_REASON_LOGOUT);
    }
    if (!isset($_COOKIE[session_name()])) {
        $url = Util::addParameter($url, session_name(), session_id());
    }
    header('Location: ' . $url);
    exit;
}

/* Redirect the user if an alternate login page has been specified. */
if (!Util::nonInputVar('RECOMPOSE')) {
    if (!empty($conf['auth']['alternate_login'])) {
        $url = Auth::addLogoutParameters($conf['auth']['alternate_login']);
        if (!isset($_COOKIE[session_name()])) {
            $url = Util::addParameter($url, session_name(), session_id(), false);
        }
        if ($url_param) {
            $url = Util::addParameter($url, 'url', $url_param, false);
        }
        header('Location: ' . $url);
        exit;
    } elseif ($conf['user']['alternate_login']) {
        $url = Auth::addLogoutParameters($conf['user']['alternate_login']);
        if (!isset($_COOKIE[session_name()])) {
            $url = Util::addParameter($url, session_name(), session_id(), false);
        }
        header('Location: ' . $url);
        exit;
    }
}

/* Initialize the password key(s). If we are doing Horde auth as well,
 * make sure that the Horde auth key gets set. */
Secret::setKey('imp');
if ($imp_auth) {
    Secret::setKey('auth');
}

$autologin = Util::getFormData('autologin', false);
$credentials = @unserialize($prefs->getValue('credentials'));
$server_key = Util::getFormData('server_key', IMP::getAutoLoginServer(true));
if (is_callable(array('Horde', 'loadConfiguration'))) {
    $result = Horde::loadConfiguration('servers.php', array('servers'));
    if (!is_a($result, 'PEAR_Error')) {
        extract($result);
    }
} else {
    require IMP_BASE . '/config/servers.php';
}
$used_servers = $servers;
if ($conf['server']['server_list'] != 'shown') {
    $used_servers = array($server_key => $servers[$server_key]);
}

if (!$logout_reason &&
    ((empty($GLOBALS['conf']['server']['change_server']) &&
      IMP::canAutoLogin($server_key, $autologin)) ||
     (!empty($GLOBALS['conf']['server']['change_server']) &&
      isset($credentials['imp'])))) {
    $url = Horde::applicationUrl('redirect.php', true);
    $params = array('actionID' => 'login', 'autologin' => true);
    if (count($used_servers) == 1) {
        $params['server_key'] = key($used_servers);
    }
    $url = Util::addParameter($url, $params, null, false);
    header('Location: ' . $url);
    exit;
}

if ($logout_reason && $imp_auth && $conf['menu']['always']) {
    $notification->push('setFocus();if (window.parent.frames.horde_menu) window.parent.frames.horde_menu.location.reload();', 'javascript');
} else {
    $notification->push('setFocus()', 'javascript');
}

if (Util::nonInputVar('RECOMPOSE')) {
    $reason = _("Please log in again to resume composing your message. If you are NOT using cookies AND you are composing messages in popup windows, you will have to log in again in your main window as well. This is to keep attackers from hijacking your session ID. We apologize for any inconvenience.");
    $title = _("Resume your session");
} else {
    $reason = $auth->getLogoutReasonString();
    $title = sprintf(_("Welcome to %s"), $registry->get('name', ($imp_auth) ? 'horde' : null));
}

if ($reason) {
    $notification->push(str_replace('<br />', ' ', $reason), 'horde.message');
}

/* Build the <select> widget for the servers and hordeauth servers lists. */
$show_list = ($conf['server']['server_list'] == 'shown');
if ($show_list) {
    $hordeauth_servers_list = $servers_list = array();
    $isAuth = Auth::isAuthenticated();
    foreach ($servers as $key => $val) {
        $entry = array(
            'sel' => IMP::isPreferredServer($val, $key),
            'val' => $key,
            'name' => $val['name']
        );

        if (empty($val['hordeauth']) || !$isAuth) {
            $servers_list[] = $entry;
        } elseif ($isAuth) {
            $hordeauth_servers_list[] = $entry;
        }
    }
}

$lang_url = null;
$choose_language = ($imp_auth && !$prefs->isLocked('language'));
if ($choose_language) {
    $_SESSION['horde_language'] = NLS::select();
    $langs = array();
    foreach ($nls['languages'] as $key => $val) {
        $langs[] = array(
            'sel' => ($key == $_SESSION['horde_language']),
            'val' => $key,
            'name' => $val
        );
    }

    if (!empty($url_param)) {
        $lang_url = urlencode($url_param);
    }
}


$protocol_list = array();
if (!empty($conf['server']['change_protocol'])) {
    $protocol = Util::getFormData('protocol', $servers[$server_key]['protocol']);
    foreach (IMP_IMAP::protocolList() as $val) {
        $protocol_list[] = array(
            'val' => $val['string'],
            'sel' => ($protocol == $val['string']),
            'name' => $val['name']
        );
    }
}

/* If DIMP/MIMP are available, show selection of alternate views. */
$views = array();
if (!empty($conf['user']['select_view'])) {
    $apps = $registry->listApps(null, true);
    $view_cookie = isset($_COOKIE['default_imp_view'])
        ? $_COOKIE['default_imp_view']
        : ($browser->isMobile() && isset($apps['mimp']) ? 'mimp' 
           : isset($conf['user']['default_view']) ? $conf['user']['default_view'] : 'imp');
    if (isset($apps['dimp']) || isset($apps['mimp'])) {
        $views[] = array('sel' => $view_cookie == 'imp',
                         'val' => 'imp', 'name' => _("Traditional"));
        if (isset($apps['dimp'])) {
            $views[] = array('sel' => $view_cookie == 'dimp',
                             'val' => 'dimp', 'name' => _("Dynamic"));
        }
        if (isset($apps['mimp'])) {
            $views[] = array('sel' => $view_cookie == 'mimp',
                             'val' => 'mimp', 'name' => _("Minimalist"));
        }
    }
}

/* Mobile login page. */
if ($browser->isMobile()) {
    require_once 'Horde/Mobile.php';
    require_once 'Horde/Notification/Listener/mobile.php';

    /* Build the <select> widget for the servers list. */
    if ($show_list) {
        $server_select = new Horde_Mobile_select('server', 'popup', _("Server:"));
        foreach ($servers_list as $val) {
            $server_select->add($val['name'], $val['val'], $val['sel']);
        }
    }

    /* Build the <select> widget containing the available protocols. */
    if (!empty($protocol_list)) {
        $protocol_select = new Horde_Mobile_select('protocol', 'popup', _("Protocol:"));
        foreach ($protocol_list as $val) {
            $protocol_select->add($val['name'], $val['val'], $val['sel']);
        }
    }

    /* Build the <select> widget containing the available languages. */
    if ($choose_language) {
        // Language names are already encoded.
        $lang_select = new Horde_Mobile_select('new_lang', 'popup', _("Language:"));
        $lang_select->set('htmlchars', true);
        foreach ($langs as $val) {
            $lang_select->add($val['name'], $val['val'], $val['sel']);
        }
    }

    /* Build the <select> widget containing the available views. */
    if (!empty($views)) {
        $view_select = new Horde_Mobile_select('select_view', 'popup', _("Mode:"));
        foreach ($views as $val) {
            $view_select->add($val['name'], $val['val'], $val['sel']);
        }
    }

    require IMP_TEMPLATES . '/login/mobile.inc';
    exit;
}

$protocol_js = array();
if (!empty($conf['server']['change_protocol']) &&
    !empty($conf['server']['change_port'])) {
    foreach (IMP_IMAP::protocolList() as $val) {
        $protocol_js[$val['string']] = $val['port'];
    }
}

$display_list = ($show_list && !empty($hordeauth_servers_list));

/* Prepare the login template. */
$t = new IMP_Template();
$t->setOption('gettext', true);
$tabindex = 0;

$t->set('action', Horde::url('redirect.php', false, -1, true));
$t->set('imp_auth', intval($imp_auth));
$t->set('formInput', Util::formInput());
$t->set('actionID', htmlspecialchars($actionID));
$t->set('url', htmlspecialchars($url_param));
$t->set('autologin', intval($autologin));
$t->set('anchor_string', htmlspecialchars(Util::getFormData('anchor_string')));
$t->set('recompose_data', htmlspecialchars($recompose_data));
$t->set('server_key', (!$display_list) ? htmlspecialchars($server_key) : null);

/* Do we need to do IE version detection? */
$t->set('ie_clientcaps', (!Auth::getAuth() && ($browser->getBrowser() == 'msie') && ($browser->getMajor() >= 5)));

$extra_hidden = array();
foreach (IMP::getComposeArgs() as $arg => $value) {
    $extra_hidden[] = array('name' => htmlspecialchars($arg), 'value' => htmlspecialchars($value));
}
$t->set('extra_hidden', $extra_hidden);

require_once 'Horde/Menu.php';
$menu = new Menu(HORDE_MENU_MASK_NONE);
$t->set('menu', $menu->render());
$t->set('title', sprintf(_("Welcome to %s"), $registry->get('name', ($imp_auth) ? 'horde' : null)));

ob_start();
$notification->notify(array('listeners' => 'status'));
$t->set('notification_output', ob_get_contents());
ob_end_clean();

$t->set('display_list', $display_list);
if ($display_list) {
    $t->set('hsl_skey_tabindex', ++$tabindex);
    $t->set('hsl', $hordeauth_servers_list);
    $t->set('hsl_tabindex', ++$tabindex);
}

$t->set('server_list', ($show_list && !empty($servers_list)));
if ($t->get('server_list')) {
    $t->set('slist_tabindex', ++$tabindex);
    $t->set('slist', $servers_list);
}

$t->set('change_server', (!empty($conf['server']['change_server'])));
if ($t->get('change_server')) {
    $t->set('server_tabindex', ++$tabindex);
    $t->set('server', htmlspecialchars(Util::getFormData('server', $servers[$server_key]['server'])));
}

$t->set('change_port', (!empty($conf['server']['change_port'])));
if ($t->get('change_port')) {
    $t->set('change_port_tabindex', ++$tabindex);
    $t->set('change_port_val', htmlspecialchars(Util::getFormData('port', $servers[$server_key]['port'])));
}

$t->set('change_protocol', !empty($conf['server']['change_protocol']));
if ($t->get('change_protocol')) {
    $protocol = Util::getFormData('protocol', $servers[$server_key]['protocol']);
    $t->set('protocol_list', $protocol_list);
    $t->set('change_protocol_tabindex', ++$tabindex);
}

$t->set('username_tabindex', ++$tabindex);
$t->set('username', htmlspecialchars(Util::getFormData('imapuser')));
$t->set('user_vinfo', null);
if (!empty($conf['hooks']['vinfo'])) {
    $t->set('user_vinfo', Horde::callHook('_imp_hook_vinfo', array('vdomain'), 'imp'));
}
$t->set('password_tabindex', ++$tabindex);

$t->set('change_smtphost', (!empty($conf['server']['change_smtphost'])));
if ($t->get('change_smtphost')) {
    $t->set('smtphost_tabindex', ++$tabindex);
    $t->set('smtphost', htmlspecialchars(Util::getFormData('smtphost', $servers[$server_key]['server'])));
    $t->set('change_smtpport', (!empty($conf['server']['change_smtpport'])));
    if ($t->get('change_smtpport')) {
        $t->set('smtpport_tabindex', ++$tabindex);
        $t->set('smtpport', htmlspecialchars(Util::getFormData('smtpport', (!empty($servers[$server_key]['smtpport'])) ? $servers[$server_key]['smtpport'] : null)));
    }
}

$t->set('choose_language', $choose_language);
if ($choose_language) {
    $t->set('langs_tabindex', ++$tabindex);
    $t->set('langs', $langs);
}

$t->set('select_view', !empty($views));
if ($t->get('select_view')) {
    $t->set('view_tabindex', ++$tabindex);
    $t->set('views', $views);
}

$t->set('login_tabindex', ++$tabindex);
$t->set('login', _("Login"));

$t->set('signup_link', false);
if ($conf['signup']['allow'] && isset($auth) && $auth->hasCapability('add')) {
    $t->set('signup_text', _("Don't have an account? Sign up."));
    $t->set('signup_link', Horde::link(Util::addParameter(Horde::url($registry->get('webroot', 'horde') . '/signup.php'), 'url', $url_param), $t->get('signup_text'), 'light'));
}

$login_page = true;
require_once IMP_BASE . '/lib/JSON.php';
Horde::addScriptFile('prototype.js', 'imp', true);
Horde::addScriptFile('login.js', 'imp', true);
require IMP_TEMPLATES . '/common-header.inc';
IMP::addInlineScript(array(
    'var autologin_url = \'' . Util::addParameter(Horde::selfUrl(), array('autologin' => $autologin, 'server_key' => '')) . '\'',
    'var show_list = ' . intval($show_list),
    'var ie_clientcaps = ' . intval($t->get('ie_clientcaps')),
    'var lang_url = ' . ((is_null($lang_url)) ? 'null' : '\'' . $lang_url . '\''),
    'var protocols = ' . IMP_Serialize_JSON::encode(String::convertCharset($protocol_js, NLS::getCharset()), 'utf-8'),
    'var change_smtphost = ' . intval(!empty($GLOBALS['conf']['server']['change_smtphost'])),
    'var imp_auth = ' . intval($imp_auth),
    'var nomenu = ' . intval(empty($conf['menu']['always'])),
));
echo $t->fetch(IMP_TEMPLATES . '/login/login.html');

if (!empty($recompose_data)) {
    /* Prepare recompose template. */
    $template = new IMP_Template();
    $template->setOption('gettext', true);
    $template->set('to_val', htmlspecialchars(_getFormData('to', $recompose_data)));
    $template->set('cc_val', htmlspecialchars(_getFormData('cc')));
    $template->set('bcc_val', htmlspecialchars(_getFormData('bcc')));
    $template->set('subject_val', htmlspecialchars(_getFormData('subject')));
    $message = _getFormData('message');
    $template->set('is_msg', !empty($message));
    if ($template->get('is_msg')) {
        $template->set('msg_val', nl2br(htmlspecialchars(_getFormData('message'))));
    }
    echo $template->fetch(IMP_TEMPLATES . '/login/recompose.html');
}

if (is_callable(array('Horde', 'loadConfiguration'))) {
    Horde::loadConfiguration('motd.php', null, null, true);
} else {
    if (is_readable(IMP_BASE . '/config/motd.php')) {
        require IMP_BASE . '/config/motd.php';
    }
}
require $registry->get('templates', 'horde') . '/common-footer.inc';

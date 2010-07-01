<?php
/**
 * IMP external API interface.
 *
 * This file defines IMP's external API interface. Other applications
 * can interact with IMP through this API.
 *
 * $Horde: imp/lib/api.php,v 1.94.10.21 2008-09-30 17:58:49 mrubinsk Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package IMP
 */

$_services['perms'] = array(
    'args' => array(),
    'type' => '{urn:horde}stringArray');

$_services['authenticate'] = array(
    'args' => array('userID' => 'string', 'credentials' => '{urn:horde}hash', 'params' => '{urn:horde}hash'),
    'checkperms' => false,
    'type' => 'boolean'
);

$_services['authCredentials'] = array(
    'args' => array(),
    'type' => '{urn:horde}hashHash'
);

$_services['getStream'] = array(
    'args' => array('mailbox' => 'string', 'flags' => 'int'),
    'type' => 'resource'
);

$_services['compose'] = array(
    'args' => array('args' => '{urn:horde}hash', 'extra' => '{urn:horde}hash'),
    'type' => 'string'
);

$_services['batchCompose'] = array(
    'args' => array('args' => '{urn:horde}hash', 'extra' => '{urn:horde}hash'),
    'type' => 'string'
);

$_services['folderlist'] = array(
    'args' => array(),
    'type' => '{urn:horde}stringArray'
);

$_services['createFolder'] = array(
    'args' => array('folder' => 'string'),
    'type' => 'string'
);

$_services['server'] = array(
    'args' => array(),
    'type' => 'string'
);

$_services['favouriteRecipients'] = array(
    'args' => array('limit' => 'int'),
    'type' => '{urn:horde}stringArray'
);

$_services['changeLanguage'] = array(
    'args' => array(),
    'type' => 'boolean'
);

if (!empty($_SESSION['imp']['admin'])) {
    $_services['userList'] = array(
        'type' => '{urn:horde}stringArray'
    );

    $_services['addUser'] = array(
        'args' => array('userId' => 'string')
    );

    $_services['removeUser'] = array(
        'args' => array('userId' => 'string')
    );
}

/**
 * Returns a list of available permissions.
 */
function _imp_perms()
{
    return array(
        'tree' => array(
            'imp' => array(
                 'create_folders' => false,
                 'max_folders' => false,
                 'max_recipients' => false,
                 'max_timelimit' => false,
             ),
        ),
        'title' => array(
            'imp:create_folders' => _("Allow Folder Creation?"),
            'imp:max_folders' => _("Maximum Number of Folders"),
            'imp:max_recipients' => _("Maximum Number of Recipients per Message"),
            'imp:max_timelimit' => _("Maximum Number of Recipients per Time Period"),
        ),
        'type' => array(
            'imp:create_folders' => 'boolean',
            'imp:max_folders' => 'int',
            'imp:max_recipients' => 'int',
            'imp:max_timelimit' => 'int',
        )
    );
}

/**
 * Tries to authenticate with the mail server and create a mail session.
 *
 * @param string $userID      The username of the user.
 * @param array $credentials  Credentials of the user. Only allowed key:
 *                            'password'.
 * @param array $params       Additional parameters. Only allowed key:
 *                            'server'.
 *
 * @return boolean  True on success, false on failure.
 */
function _imp_authenticate($userID, $credentials, $params = array())
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';
    require_once IMP_BASE . '/lib/Session.php';

    $server_key = empty($params['server'])
        ? IMP::getAutoLoginServer(true)
        : $params['server'];

    /* Read the required server parameters from the servers.php file. */
    if (is_callable(array('Horde', 'loadConfiguration'))) {
        $servers = Horde::loadConfiguration('servers.php', 'servers');
        if (is_a($servers, 'PEAR_Error')) {
            $servers = array();
        }
    } else {
        require IMP_BASE . '/config/servers.php';
    }

    return IMP_Session::createSession($userID, $credentials['password'], $server_key, empty($result[$server_key]) ? array() : $result[$server_key]);
}

/**
 * Returns a list of authentication credentials, i.e. server settings that can
 * be specified by the user on the login screen.
 *
 * @return array  A hash with credentials, suited for the preferences
 *                interface.
 */
function _imp_authCredentials()
{
    require_once dirname(__FILE__) . '/IMAP.php';

    $protocol_list = array();
    foreach (IMP_IMAP::protocolList() as $val) {
        $protocol_list[$val['string']] = $val['name'];
    }
    $params = array(
        'server' => array(
            'desc' => _("Server"),
            'type' => 'text'),
        'port' => array(
            'desc' => _("Port"),
            'type' => 'number',
            'value' => 143),
        'protocol' => array(
            'desc' => _("Protocol"),
            'type' => 'enum',
            'enum' => $protocol_list,
            'value' => 'imap/notls'),
        'smtphost' => array(
            'desc' => _("Outbound Server"),
            'type' => 'text'),
        'smtpport' => array(
            'desc' => _("SMTP Port"),
            'type' => 'number',
            'value' => 25));

    $app_name = $GLOBALS['registry']->get('name');
    $credentials = array(
        'username' => array(
            'desc' => sprintf(_("%s for %s"), _("Username"), $app_name),
            'type' => 'text'),
        'password' => array(
            'desc' => sprintf(_("%s for %s"), _("Password"), $app_name),
            'type' => 'password'));

    foreach ($params as $name => $param) {
        if (!empty($GLOBALS['conf']['server']['change_' . $name])) {
            $param['desc'] = sprintf(_("%s for %s"), $param['desc'], $app_name);
            $credentials[$name] = $param;
        }
    }

    return $credentials;
}

/**
 * Attempts to authenticate via IMP and return an IMAP stream.
 *
 * @param string $mailbox  The mailbox name.
 * @param int $flags       IMAP connection flags.
 *
 * @return mixed  An IMAP resource on success, false on failure.
 */
function _imp_getStream($mailbox = null, $flags = 0)
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';

    if (IMP::checkAuthentication(true)) {
        $imap = &IMP_IMAP::singleton();
        if ($imap->changeMbox($mailbox, $flags)) {
            return $imap->stream();
        }
    }

    return false;
}

/**
 * Returns a compose window link.
 *
 * @param string|array $args  List of arguments to pass to compose.php.
 *                            If this is passed in as a string, it will be
 *                            parsed as a toaddress?subject=foo&cc=ccaddress
 *                            (mailto-style) string.
 * @param array $extra        Hash of extra, non-standard arguments to pass to
 *                            compose.php.
 *
 * @return string  The link to the message composition screen.
 */
function _imp_compose($args = array(), $extra = array())
{
    $link = _imp_batchCompose(array($args), array($extra));
    return $link[0];
}

/**
 * Return a list of compose window links.
 *
 * @param mixed $args   List of lists of arguments to pass to compose.php. If
 *                      the lists are passed in as strings, they will be parsed
 *                      as toaddress?subject=foo&cc=ccaddress (mailto-style)
 *                      strings.
 * @param array $extra  List of hashes of extra, non-standard arguments to pass
 *                      to compose.php.
 *
 * @return string  The list of links to the message composition screen.
 */
function _imp_batchCompose($args = array(), $extra = array())
{
    if (isset($_SESSION['imp']['viewmode']) &&
        $_SESSION['imp']['viewmode'] != 'imp') {
        return $GLOBALS['registry']->callByPackage($_SESSION['imp']['viewmode'], 'batchCompose', array($args, $extra));
    }

    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';

    $links = array();
    foreach ($args as $i => $arg) {
        $links[$i] = IMP::composeLink($arg, !empty($extra[$i]) ? $extra[$i] : array());
    }

    return $links;
}

/**
 * Returns the list of folders.
 *
 * @return array  The list of IMAP folders or false if not available.
 */
function _imp_folderlist()
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';

    $result = false;

    if (IMP::checkAuthentication(true)) {
        if ($_SESSION['imp']['base_protocol'] == 'pop3') {

            $result = array('INBOX' => array('val' => 'INBOX', 'label' => _("Inbox"), 'abbrev' => 'INBOX'));
        } else {
            require_once IMP_BASE . '/lib/Folder.php';
            $imp_folder = &IMP_Folder::singleton();
            $result = $imp_folder->flist_IMP();
        }
    }

    return $result;
}

/**
 * Creates a new folder.
 *
 * @param string $folder  The UTF7-IMAP encoded name of the folder to create.
 *
 * @return string  The full folder name created on success, an empty string
 *                 on failure.
 */
function _imp_createFolder($folder)
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';

    $result = false;

    if (IMP::checkAuthentication(true)) {
        require_once IMP_BASE . '/lib/Folder.php';
        $imp_folder = &IMP_Folder::singleton();
        $result = $imp_folder->create(IMP::appendNamespace($folder), $GLOBALS['prefs']->getValue('subscribe'));
    }

    return (empty($result)) ? '' : $folder;
}

/**
 * Returns the currently logged on IMAP server.
 *
 * @return string  The server hostname.  Returns null if the user has not
 *                 authenticated into IMP yet.
 */
function _imp_server()
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';
    return (IMP::checkAuthentication(true)) ? $_SESSION['imp']['server'] : null;
}

/**
 * Returns the list of favorite recipients.
 *
 * @param integer $limit  Return this number of recipients.
 * @param array $filter   A list of messages types that should be returned.
 *                        A value of null returns all message types.
 *
 * @return array  A list with the $limit most favourite recipients.
 */
function _imp_favouriteRecipients($limit,
                                  $filter = array('new', 'forward', 'reply', 'redirect'))
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';

    if ($GLOBALS['conf']['sentmail']['driver'] != 'none') {
        require_once IMP_BASE . '/lib/Sentmail.php';
        $sentmail = IMP_Sentmail::factory();
        return $sentmail->favouriteRecipients($limit, $filter);
    }

    return array();
}

/**
 * Performs tasks necessary when the language is changed during the session.
 */
function _imp_changeLanguage()
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_view'] = true;
    require_once dirname(__FILE__) . '/base.php';

    if (IMP::checkAuthentication(true)) {
        require_once IMP_BASE . '/lib/Folder.php';
        require_once IMP_BASE . '/lib/Search.php';
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imp_folder = &IMP_Folder::singleton();
        $imp_folder->clearFlistCache();
        $imptree = &IMP_Tree::singleton();
        $imptree->init();
        $imp_search = new IMP_Search();
        $imp_search->sessionSetup(true);
    }
}

/**
 * Adds a set of authentication credentials.
 *
 * @param string $userId  The userId to add.
 *
 * @return boolean  True on success or a PEAR_Error object on failure.
 */
function _imp_addUser($userId)
{
    return _imp_adminDo('add', array($userId));
}

/**
 * Deletes a set of authentication credentials.
 *
 * @param string $userId  The userId to delete.
 *
 * @return boolean  True on success or a PEAR_Error object on failure.
 */
function _imp_removeUser($userId)
{
    return _imp_adminDo('remove', array($userId));
}

/**
 * Lists all users in the system.
 *
 * @return array  The array of userIds, or a PEAR_Error object on failure.
 */
function _imp_userList()
{
    return _imp_adminDo('list', array());
}

/**
 * Private function to perform an admin event.
 */
function _imp_adminDo($task, $params)
{
    require_once 'Horde/IMAP/Admin.php';
    require_once 'Horde/Secret.php';

    $admin_params = $_SESSION['imp']['admin']['params'];
    $admin_params['admin_user'] = $admin_params['login'];
    $admin_params['admin_password'] = Secret::read(Secret::getKey('imp'), $admin_params['password']);
    $imap = new IMAP_Admin($admin_params);

    switch ($task) {
    case 'add':
        return $imap->addMailbox(String::convertCharset($params[0], NLS::getCharset(), 'utf7-imap'));

    case 'remove':
        return $imap->removeMailbox(String::convertCharset($params[0], NLS::getCharset(), 'utf7-imap'));

    case 'list':
        return $imap->listMailboxes();
    }
}

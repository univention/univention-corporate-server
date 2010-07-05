<?php
/**
 * $Horde: dimp/lib/DIMP.php,v 1.110.2.38 2009-04-07 04:52:58 slusarz Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */
class DIMP {

    /**
     * Output a dimp-style action (menubar) link.
     *
     * @param array $params  A list of parameters.
     * <pre>
     * 'app' - The application to load the icon from.
     * 'class' - The CSS classname to use for the link.
     * 'icon' - The icon filename to display.
     * 'id' - The DOM ID of the link.
     * 'title' - The title string.
     * 'tooltip' - Tooltip text to use.
     * </pre>
     *
     * @return string  An HTML link to $url.
     */
    function actionButton($params = array())
    {
        $tooltip = (empty($params['tooltip'])) ? '' : $params['tooltip'];

        if (empty($params['title'])) {
            static $charset;
            if (!isset($charset)) {
                $charset = NLS::getCharset();
            }
            $old_error = error_reporting(0);
            $tooltip = nl2br(htmlspecialchars($tooltip, ENT_QUOTES, $charset));
            $title = '';
        } else {
            $title = $params['title'];
        }

        return Horde::link('', $tooltip, empty($params['class']) ? '' : $params['class'], '', '', '', '',
                           empty($params['id']) ? array() : array('id' => $params['id']),
                           !empty($title))
            . (!empty($params['icon'])
               ? Horde::img($params['icon'], $title, '',
                            $GLOBALS['registry']->getImageDir(empty($params['app']) ? 'dimp' : $params['app']))
               : '') . $title . '</a>';
    }

    /**
     * Output everything up to but not including the <body> tag.
     *
     * @param string $title   The title of the page.
     * @param array $scripts  Any additional scripts that need to be loaded.
     *                        Each entry contains the three elements necessary
     *                        for a Horde::addScriptFile() call.
     */
    function header($title, $scripts = array())
    {
        // Don't autoload any javascript files.
        Horde::disableAutoloadHordeJS();

        // Need to include script files before we start output
        Horde::addScriptFile('prototype.js', 'horde', true);
        Horde::addScriptFile('effects.js', 'imp', true);

        // ContextSensitive must be loaded before DimpCore.
        while (list($key, $val) = each($scripts)) {
            if (($val[0] == 'ContextSensitive.js') &&
                ($val[1] == 'dimp')) {
                Horde::addScriptFile($val[0], $val[1], $val[2]);
                unset($scripts[$key]);
                break;
            }
        }
        Horde::addScriptFile('DimpCore.js', 'dimp', true);

        // Add other scripts now
        foreach ($scripts as $val) {
            call_user_func_array(array('Horde', 'addScriptFile'), $val);
        }

        $page_title = $GLOBALS['registry']->get('name');
        if (!empty($title)) {
            $page_title .= ' :: ' . $title;
        }

        if (isset($GLOBALS['language'])) {
            header('Content-type: text/html; charset=' . NLS::getCharset());
            header('Vary: Accept-Language');
        }

        echo '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">' . "\n" .
             (!empty($GLOBALS['language']) ? '<html lang="' . strtr($GLOBALS['language'], '_', '-') . '"' : '<html') . ">\n".
             "<head>\n";

        // TODO: Make dimp work with IE 8 standards mode
        if ($GLOBALS['browser']->isBrowser('msie') &&
            ($GLOBALS['browser']->getMajor() == 8)) {
            echo '<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE7" />' . "\n";
        }

        echo '<title>' . htmlspecialchars($page_title) . "</title>\n" .
             '<link href="' . $GLOBALS['registry']->getImageDir() . "/favicon.ico\" rel=\"SHORTCUT ICON\" />\n".
             IMP::wrapInlineScript(DIMP::_includeDIMPJSVars());

        IMP::includeStylesheetFiles(true, 'dimp');

        echo "</head>\n";

        // Send what we have currently output so the browser can start
        // loading CSS/JS. See:
        // http://developer.yahoo.com/performance/rules.html#flush
        flush();
    }

    /**
     * Outputs the javascript code which defines all javascript variables
     * that are dependent on the local user's account.
     *
     * @private
     *
     * @return string
     */
    function _includeDIMPJSVars()
    {
        global $browser, $conf, $dimp_conf, $dimp_prefs, $prefs, $registry;

        require_once 'Horde/Serialize.php';

        $compose_mode = (strstr($_SERVER['PHP_SELF'], 'compose.php') || strstr($_SERVER['PHP_SELF'], 'message.php'));
        $dimp_webroot = $registry->get('webroot', 'dimp');
        $horde_webroot = $registry->get('webroot', 'horde');

        $app_urls = $code = array();

        foreach (DIMP::menuList() as $app) {
            $app_urls[$app] = Horde::url($registry->getInitialPage($app), true);
        }

        require DIMP_BASE . '/config/portal.php';
        foreach ($dimp_block_list as $block) {
            if (is_a($block['ob'], 'Horde_Block')) {
                $app = $block['ob']->getApp();
                if (empty($app_urls[$app])) {
                    $app_urls[$app] = Horde::url($registry->getInitialPage($app), true);
                }
            }
        }

        /* Variables used in core javascript files. */
        $code['conf'] = array(
            'URI_DIMP_INBOX' => Horde::url($dimp_webroot . '/index.php', true, -1),
            'URI_IMP' => Horde::url($dimp_webroot . '/imp.php', true, -1),
            'URI_PREFS' => Horde::url($horde_webroot . '/services/prefs/', true, -1),
            'SESSION_ID' => defined('SID') ? SID : '',

            'app_urls' => $app_urls,
            'timeout_url' => Auth::addLogoutParameters($horde_webroot . '/login.php', AUTH_REASON_SESSION),
            'message_url' => Horde::url($dimp_webroot . '/message.php'),
            'compose_url' => Horde::url($dimp_webroot . '/compose.php'),
            'prefs_url' => str_replace('&amp;', '&', Horde::getServiceLink('options', 'dimp')),
	    'folder_rights' => Util::addParameter(Horde::url($registry->get('webroot', 'imp') . '/acl.php', true), array('app' => 'imp', 'group'=> 'acl'), null, false),

            'sortthread' => SORTTHREAD,
            'sortdate' => SORTDATE,

            'idx_sep' => IMP_IDX_SEP,

            'popup_width' => 820,
            'popup_height' => 610,

            'forward_default' => $prefs->getValue('forward_default'),
            'spam_folder' => IMP::folderPref($prefs->getValue('spam_folder'), true),
            'spam_reporting' => (int) !empty($conf['spam']['reporting']),
            'spam_spamfolder' => (int) !empty($conf['spam']['spamfolder']),
            'ham_reporting' => (int) !empty($conf['notspam']['reporting']),
            'ham_spamfolder' => (int) !empty($conf['notspam']['spamfolder']),
            'refresh_time' => (int) $prefs->getValue('refresh_time'),
            'search_all' => (int) !empty($conf['search']['search_all']),

            'fixed_folders' => empty($conf['server']['fixed_folders'])
                ? array()
                : array_map(array('DIMP', '_appendedFolderPref'), $conf['server']['fixed_folders']),

            'name' => $registry->get('name', 'dimp'),

            'preview_pref' => (bool)$dimp_prefs->getValue('show_preview'),

            'is_ie6' => ($browser->isBrowser('msie') && ($browser->getMajor() < 7)),

            'buffer_pages' => intval($dimp_conf['viewport']['buffer_pages']),
            'limit_factor' => intval($dimp_conf['viewport']['limit_factor']),
            'viewport_wait' => intval($dimp_conf['viewport']['viewport_wait']),
            'login_view' => $dimp_prefs->getValue('login_view'),
            'background_inbox' => !empty($dimp_conf['viewport']['background_inbox']),

            // Turn debugging on?
            'debug' => !empty($dimp_conf['js']['debug']),
        );

        /* Gettext strings used in core javascript files. */
        $code['text'] = array_map('addslashes', array(
            'portal' => _("Portal"),
            'prefs' => _("User Options"),
            'search' => _("Search"),
            'resfound' => _("results found"),
            'message' => _("Message"),
            'messages' => _("Messages"),
            'of' => _("of"),
            'nomessages' => _("No Messages"),
            'hidetext' => _("Hide Quoted Text"),
            'showtext' => _("Show Quoted Text"),
            'lines' => _("lines"),
            'ok' => _("Ok"),
            'copyto' => _("Copy %s to %s"),
            'moveto' => _("Move %s to %s"),
            'baselevel' => _("base level of the folder tree"),
            'cancel' => _("Cancel"),
            'loading' => _("Loading..."),
            'check' => _("Checking..."),
            'getmail' => _("Get Mail"),
            'ajax_timeout' => _("There has been no contact with the remote server for several minutes. The server may be temporarily unavailable or network problems may be interrupting your session. You will not see any updates until the connection is restored."),
            'ajax_recover' => _("The connection to the remote server has been restored."),
            'listmsg_wait' => _("The server is still generating the message list."),
            'listmsg_timeout' => _("The server was unable to generate the message list. Please try again later."),
            'popup_block' => _("A popup window could not be opened. Your browser may be blocking popups."),
            'hide_preview' => _("Hide Preview"),
            'show_preview' => _("Show Preview"),
            'rename_prompt' => _("Rename folder to:"),
            'create_prompt' => _("Create folder:"),
            'createsub_prompt' => _("Create subfolder:"),
            'empty_folder' => _("Permanently delete all messages?"),
            'delete_folder' => _("Permanently delete this folder?"),
        ));

        if ($compose_mode) {
            /* Variables used in compose page. */
            $compose_cursor = $GLOBALS['prefs']->getValue('compose_cursor');
            $code['conf_compose'] = array(
                'rte_avail' => $browser->hasFeature('rte'),
                'cc' => (bool) $prefs->getValue('compose_cc'),
                'bcc' => (bool) $prefs->getValue('compose_bcc'),
                'attach_limit' => ($conf['compose']['attach_count_limit'] ? intval($conf['compose']['attach_count_limit']) : -1),
                'close_draft' => $prefs->getValue('close_draft'),
                'js_editor' => $prefs->getValue('jseditor'),
                'compose_cursor' => ($compose_cursor ? $compose_cursor : 'top'),

                'abook_url' => Horde::url($GLOBALS['registry']->get('webroot', 'imp') . '/contacts.php'),
                'specialchars_url' => Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/keyboard.php'),
            );

            /* Gettext strings used in compose page. */
            $code['text_compose'] = array_map('addslashes', array(
                'cancel' => _("Cancelling this message will permanently discard its contents and will delete auto-saved drafts.\nAre you sure you want to do this?"),
                'nosubject' => _("The message does not have a Subject entered.") . "\n" . _("Send message without a Subject?"),
                'fillform' => _("You have already changed the message body, are you sure you want to drop the changes?"),
                'remove' => _("remove"),
                'uploading' => _("Uploading..."),
                'attachment_limit' => _("The attachment limit has been reached."),
                'sending' => _("Sending..."),
                'saving' => _("Saving..."),
                'toggle_html' => _("Really discard all formatting information? This operation cannot be undone."),
            ));
        }

        return array('var DIMP = ' . Horde_Serialize::serialize($code, SERIALIZE_JSON, NLS::getCharset()) . ';');
    }

    /**
     * Return an appended IMP folder string
     */
    function _appendedFolderPref($folder)
    {
        return IMP::folderPref($folder, true);
    }

    /**
     * Return the javascript code necessary to display notification popups.
     *
     * @return string  The notification JS code.
     */
    function notify()
    {
        $GLOBALS['notification']->notify(array('listeners' => 'status'));
        $msgs = $GLOBALS['dimp_listener']->getStack(true);
        if (!count($msgs)) {
            return '';
        }

        require_once 'Horde/Serialize.php';
        return 'DimpCore.showNotifications(' . Horde_Serialize::serialize($msgs, SERIALIZE_JSON) . ')';
    }

    /**
     * Output the javascript for the page.
     */
    function outputJS()
    {
        IMP::includeScriptFiles();
        IMP::outputInlineScript();
    }

    /**
     * Formats the response to send to javascript code when dealing with
     * folder operations.
     *
     * @param IMP_Tree $imptree  An IMP_Tree object.
     * @param array $changes     An array with three sub arrays - to be used
     *                           instead of the return from
     *                           $imptree->eltDiff():
     *                           'a' - a list of folders to add
     *                           'c' - a list of changed folders
     *                           'd' - a list of folders to delete
     *
     * @return array  The object used by the JS code to update the folder tree.
     */
    function getFolderResponse($imptree, $changes = null)
    {
        if ($changes === null) {
            $changes = $imptree->eltDiff();
        }
        if (empty($changes)) {
            return false;
        }

        $result = array('a' => array(), 'c' => array(), 'd' => array());

        foreach ($changes['a'] as $val) {
            $result['a'][] = DIMP::_createFolderElt($imptree->element($val));
        }

        foreach ($changes['c'] as $val) {
            // Skip the base element, since any change there won't ever be
            // updated on-screen.
            if ($val == IMPTREE_BASE_ELT) {
                continue;
            }
            $result['c'][] = DIMP::_createFolderElt($imptree->element($val));
        }

        foreach (array_reverse($changes['d']) as $val) {
            $result['d'][] = rawurlencode($val);
        }

        return $result;
    }

    /**
     * Create an object used by DimpCore to generate the folder tree.
     *
     * @access private
     *
     * @param array $elt  The output from IMP_Tree::element().
     *
     * @return stdClass  The element object. Contains the following items:
     * <pre>
     * 'ch' (children) = Does the folder contain children? [boolean]
     *                   [DEFAULT: no]
     * 'cl' (class) = The CSS class. [string] [DEFAULT: 'base']
     * 'co' (container) = Is this folder a container element? [boolean]
     *                    [DEFAULT: no]
     * 'i' (icon) = A user defined icon to use. [string] [DEFAULT: none]
     * 'l' (label) = The folder display label. [string]
     * 'm' (mbox) = The mailbox value. [string]
     * 'pa' (parent) = The parent element. [string]
     * 'po' (polled) = Is the element polled? [boolean] [DEFAULT: no]
     * 's' (special) = Is this a "special" element? [boolean] [DEFAULT: no]
     * 'u' (unseen) = The number of unseen messages. [integer]
     * </pre>
     */
    function _createFolderElt($elt)
    {
        $ob = new stdClass;
        if ($elt['children']) {
           $ob->ch = 1;
        }
        $ob->l = $elt['base_elt']['l'];
        $ob->m = rawurlencode($elt['value']);
        $ob->pa = rawurlencode($elt['parent']);
        if ($elt['polled']) {
            $ob->po = 1;
        }

        if ($elt['container']) {
            $ob->co = 1;
            $ob->cl = 'exp';
        } else {
            if ($elt['polled']) {
                $ob->u = $elt['unseen'];
            }

            switch ($elt['special']) {
            case IMPTREE_SPECIAL_INBOX:
                $ob->cl = 'inbox';
                $ob->s = 1;
                break;

            case IMPTREE_SPECIAL_TRASH:
                $ob->cl = 'trash';
                $ob->s = 1;
                break;

            case IMPTREE_SPECIAL_SPAM:
                $ob->cl = 'spam';
                $ob->s = 1;
                break;

            case IMPTREE_SPECIAL_DRAFT:
                $ob->cl = 'drafts';
                $ob->s = 1;
                break;

            case IMPTREE_SPECIAL_SENT:
                $ob->cl = 'sent';
                $ob->s = 1;
                break;

            default:
                if (!empty($elt['vfolder'])) {
                    // TODO: Add Virtual Folder menus.
                    if ($GLOBALS['imp_search']->isVTrashFolder($elt['value'])) {
                        $ob->cl = 'trash';
                    } elseif ($GLOBALS['imp_search']->isVINBOXFolder($elt['value'])) {
                        $ob->cl = 'inbox';
                    }
                } elseif ($elt['children']) {
                    $ob->cl = 'exp';
                }
                break;
            }
        }

        if ($elt['user_icon']) {
            $ob->cl = 'customimg';
            $dir = empty($elt['icondir'])
                ? $GLOBALS['registry']->getImageDir()
                : $elt['icondir'];
            $ob->i = empty($dir)
                ? $elt['icon']
                : $dir . '/' . $elt['icon'];
        }

        return $ob;
    }

    /**
     * Returns a stdClass response object with added notification information.
     *
     * @param string $data     The 'response' data.
     * @param boolean $notify  If true, adds notification information to
     *                         object.
     * @param boolean $auto    If true, DimpCore will automatically display the
     *                         notification.  If false, the callback handler
     *                         is responsible for displaying the notification.
     */
    function prepareResponse($data = null, $notify = true, $auto = true)
    {
        $response = new stdClass();
        $response->response = $data;
        if ($notify) {
            $GLOBALS['notification']->notify(array('listeners' => 'status'));
            $stack = $GLOBALS['dimp_listener']->getStack();
            if (!empty($stack)) {
                $response->msgs = $GLOBALS['dimp_listener']->getStack();
                if (!(bool)$auto) {
                    $response->msgs_noauto = true;
                }
            }
        }
        return $response;
    }

    /**
     * Return information about the current attachments for a message
     *
     * @var object IMP_Compose $imp_compose  An IMP_Compose object.
     *
     * @return array  An array of arrays with the following keys:
     * <pre>
     * 'number' - The current attachment number
     * 'name' - The HTML encoded attachment name
     * 'type' - The MIME type of the attachment
     * 'size' - The size of the attachment in KB (string)
     * </pre>
     */
    function getAttachmentInfo($imp_compose)
    {
        $fwd_list = array();

        if ($imp_compose->numberOfAttachments()) {
            foreach ($imp_compose->getAttachments() as $file_num => $mime) {
                $fwd_list[] = array(
                    'number' => $file_num,
                    'name' => htmlspecialchars($mime->getName(true, true)),
                    'type' => $mime->getType(),
                    'size' => $mime->getSize()
                );
            }
        }

        return $fwd_list;
    }

    /**
     * Return a list of DIMP specific menu items.
     *
     * @return array  The array of menu items.
     */
    function menuList()
    {
        if (isset($GLOBALS['dimp_conf']['menu']['apps'])) {
            $apps = $GLOBALS['dimp_conf']['menu']['apps'];
            if (is_array($apps) && count($apps)) {
                return $apps;
            }
        }
        return array();
    }

    /**
     * Returns the appropriate link to call the message composition screen.
     *
     * @param mixed $args   List of arguments to pass to compose.php. If this
     *                      is passed in as a string, it will be parsed as a
     *                      toaddress?subject=foo&cc=ccaddress (mailto-style)
     *                      string.
     * @param array $extra  Hash of extra, non-standard arguments to pass to
     *                      compose.php.
     *
     * @return string  The link to the message composition screen.
     */
    function composeLink($args = array(), $extra = array())
    {
        // IE 6 & 7 handles window.open() URL param strings differently if
        // triggered via an href or an onclick.  Since we have no hint
        // at this point where this link will be used, we have to always
        // encode the params and explicitly call rawurlencode() in
        // compose.php.
        $args = IMP::composeLinkArgs($args, $extra);
        $encode_args = array();
        foreach ($args as $k => $v) {
            $encode_args[$k] = rawurlencode($v);
        }
        return 'javascript:void(window.open(\'' . Util::addParameter(Horde::applicationUrl('compose.php'), $encode_args, null, false) . '\', \'\', \'width=820,height=610,status=1,scrollbars=yes,resizable=yes\'));';
    }

}

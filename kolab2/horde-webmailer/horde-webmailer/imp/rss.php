<?php
/**
 * $Horde: imp/rss.php,v 1.11.2.6 2009-01-06 15:24:02 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Eric Garrido <ekg2002@columbia.edu>
 * @since  IMP 4.2
 */

$authentication = 'none';
@define('AUTH_HANDLER', true);
@define('IMP_BASE', dirname(__FILE__));
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Mailbox.php';
require_once IMP_BASE . '/lib/Template.php';

$auth = &Auth::singleton($conf['auth']['driver']);
if ((!Auth::getAuth() || !IMP::checkAuthentication(true)) &&
    (!isset($_SERVER['PHP_AUTH_USER']) ||
     !$auth->authenticate($_SERVER['PHP_AUTH_USER'], array('password' => isset($_SERVER['PHP_AUTH_PW']) ? $_SERVER['PHP_AUTH_PW'] : null)))) {
    header('WWW-Authenticate: Basic realm="IMP RSS Interface"');
    header('HTTP/1.0 401 Unauthorized');
    echo '401 Unauthorized';
    exit;
}

$items = array();
$mailbox = 'INBOX';
$new_mail = $request = $searchid = false;
$unseen_num = 0;

/* Determine the mailbox that was requested and if only new mail should be
 * displayed. Default to new mail in INBOX. */
$request = IMP::getPathInfo();
if (!empty($request)) {
    $request_parts = explode('/-/', $request);
    if (!empty($request_parts[0])) {
        $ns_info = IMP::getNamespace();
        $mailbox = IMP::appendNamespace(preg_replace('/\//', $ns_info['delimiter'], trim($request_parts[0], '/')));

        /* Make sure mailbox exists or else exit immediately. */
        require_once IMP_BASE . '/lib/Folder.php';
        $imp_folder = &IMP_Folder::singleton();
        if (!$imp_folder->exists($mailbox)) {
            exit;
        }
    }
    $new_mail = (isset($request_parts[1]) && ($request_parts[1] === 'new'));
}

/* Obtain some information describing the mailbox state. */
$imp_mailbox = &IMP_Mailbox::singleton($mailbox);
$total_num = $imp_mailbox->getMessageCount();
$unseen_num = ($imp_search->isVINBOXFolder($mailbox))
    ? $imp_mailbox->getMessageCount()
    : $imp_mailbox->unseenMessages(true);

require_once IMP_BASE . '/lib/IMAP/Search.php';
$query = new IMP_IMAP_Search_Query();
if ($new_mail) {
    $query->seen(false);
}
$ids = $imp_search->runSearchQuery($query, IMP::serverString($mailbox), SORTDATE, 1);

if (!empty($ids)) {
    require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
    $msg_cache = &IMP_MessageCache::singleton();
    $overview = $msg_cache->retrieve($mailbox, array_slice($ids, 0, 20), 1 | 64);
    foreach ($overview as $ob) {
        $items[] = array_map('htmlspecialchars', array(
            'title' => isset($ob->subject) ? MIME::decode($ob->subject) : _("[No Subject]"),
            'pubDate' => isset($ob->date) ? date('r', strtotime($ob->date)) : 0,
            'description' => isset($ob->preview) ? $ob->preview : '',
            'url' => Horde::applicationURL(IMP::generateIMPUrl('message.php', $mailbox, $ob->uid, $mailbox), true, -1),
            'fromAddr' => isset($ob->from) ? $ob->from : '',
            'toAddr' => isset($ob->to) ? $ob->to : '',
        ));
    }
}

$description = ($total_num == 0)
    ? _("No Messages")
    : sprintf(_("%u of %u messages in %s unread."), $unseen_num, $total_num, IMP::getLabel($mailbox));

$t = new IMP_Template();
$t->set('charset', NLS::getCharset());
$t->set('xsl', $registry->get('themesuri') . '/feed-rss.xsl');
$t->set('pubDate', htmlspecialchars(date('r')));
$t->set('desc', htmlspecialchars($description));
$t->set('title', htmlspecialchars($registry->get('name') . ' - ' . IMP::getLabel($mailbox)));
$t->set('items', $items, true);
$t->set('url', htmlspecialchars(Horde::applicationURL(IMP::generateIMPUrl('message.php', $mailbox), true, -1)));
$t->set('rss_url', htmlspecialchars(Horde::applicationUrl('rss.php', true, -1)));
$browser->downloadHeaders('mailbox.rss', 'text/xml', true);
echo $t->fetch(IMP_TEMPLATES . '/rss/mailbox.rss');

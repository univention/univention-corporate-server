<?php
/**
 * Mailbox display page.
 *
 * Parameters:
 *   'a' = actionID
 *   'p' = page
 *   's' = start
 *   'sb' = change sort: by
 *   'sd' = change sort: dir
 *
 * $Horde: mimp/mailbox.php,v 1.57.2.13 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

$load_imp = true;
@define('MIMP_BASE', dirname(__FILE__));
require_once MIMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Mailbox.php';
require_once 'Horde/MIME.php';

/* Set the current time zone. */
NLS::setTimeZone();

/* Run through the action handlers */
$actionID = Util::getFormData('a');
switch ($actionID) {
// 'm' = message missing
case 'm':
    $notification->push(_("There was an error viewing the requested message."), 'horde.error');
    break;

// 'e' = expunge mailbox
case 'e':
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = new IMP_Message();
    $imp_message->expungeMailbox(array($imp_mbox['mailbox'] => 1));
    break;

// 'c' = change sort
case 'c':
    IMP::setSort(Util::getFormData('sb'), Util::getFormData('sd'));
    break;
}

/* Initialize the user's identities. */
require_once 'Horde/Identity.php';
$identity = &Identity::singleton(array('imp', 'imp'));

/* Get the base URL for this page. */
$mailbox_url = MIMP::generateMIMPUrl('mailbox.php', $imp_mbox['mailbox']);

/* Build the list of messages in the mailbox. */
$imp_mailbox = &IMP_Mailbox::singleton($imp_mbox['mailbox']);
$pageOb = $imp_mailbox->buildMailboxPage(Util::getFormData('p'), Util::getFormData('s'));

/* Generate page links. */
$pages_first = $pages_prev = $pages_last = $pages_next = null;
if ($pageOb->page != 1) {
    $pages_first = new Horde_Mobile_link(_("First Page"), Util::addParameter($mailbox_url, 'p', 1));
    $pages_prev = new Horde_Mobile_link(_("Previous Page"), Util::addParameter($mailbox_url, 'p', $pageOb->page - 1));
}
if ($pageOb->page != $pageOb->pagecount) {
    $pages_next = new Horde_Mobile_link(_("Next Page"), Util::addParameter($mailbox_url, 'p', $pageOb->page + 1));
    $pages_last = new Horde_Mobile_link(_("Last Page"), Util::addParameter($mailbox_url, 'p', $pageOb->pagecount));
}

/* Generate mailbox summary string. */
$title = IMP::getLabel($imp_mbox['mailbox']);
$m->set('title', $title);
if ($pageOb->msgcount) {
    $msgcount = $pageOb->msgcount;
    $unseen = $imp_mailbox->unseenMessages(true);
}

$charset = NLS::getCharset();
$curr_time = time();
$curr_time -= $curr_time % 60;
$msgs = array();
$sortpref = IMP::getSort($imp_mbox['mailbox']);

require_once IMP_BASE . '/lib/UI/Mailbox.php';
$imp_ui = new IMP_UI_Mailbox($imp_mbox['mailbox'], $charset, $identity);

/* Build the array of message information. */
$mailboxOverview = $imp_mailbox->getMailboxArray(range($pageOb->begin, $pageOb->end));
if ($sortpref['by'] == SORTTHREAD) {
    $uid_list = array();
    foreach ($mailboxOverview as $val) {
        $uid_list[] = $val->uid;
    }
    $threadob = $imp_mailbox->getThreadOb();
}

foreach ($mailboxOverview as $msgIndex => $ob) {
    /* Initialize the header fields. */
    $msg = array(
        'number' => $ob->msgno,
        'status' => ''
    );

    /* Format the from header. */
    $from_res = (isset($ob->getfrom)) ? $ob->getfrom : $imp_ui->getFrom($ob);
    $msg['from'] = $from_res['from'];
    if (String::length($msg['from']) > $mimp_conf['mailbox']['max_from_chars']) {
        $msg['from'] = String::substr($msg['from'], 0, $mimp_conf['mailbox']['max_from_chars']) . '...';
    }

    $msg['subject'] = (!empty($ob->subject))
        ? $imp_ui->getSubject($ob->subject)
        : _("[No Subject]");

    if (($sortpref['by'] == SORTTHREAD) &&
        ($threadob->getThreadIndent($ob->uid) - 1)) {
        $msg['subject'] = '>> ' . ltrim($msg['subject']);
    }

    if (String::length($msg['subject']) > $mimp_conf['mailbox']['max_subj_chars']) {
        $msg['subject'] = String::substr($msg['subject'], 0, $mimp_conf['mailbox']['max_subj_chars']) . '...';
    }

    /* Generate the target link. */
    $target = MIMP::generateMIMPUrl('message.php', $imp_mbox['mailbox'], $ob->uid, $ob->mailbox);

    /* Get flag information. */
    if ($_SESSION['imp']['base_protocol'] != 'pop3') {
        if (!empty($ob->to) && $identity->hasAddress(IMP::bareAddress($ob->to))) {
            $msg['status'] .= '+';
        }
        if (!$ob->seen) {
            $msg['status'] .= 'N';
        }
        if ($ob->answered) {
            $msg['status'] .= 'r';
        }
        if ($ob->draft) {
            $target = MIMP::composeLink(array(), array('a' => 'd', 'thismailbox' => $imp_mbox['mailbox'], 'index' => $ob->uid, 'bodypart' => 1));
        }
        if ($ob->flagged) {
            $msg['status'] .= 'I';
        }
        if ($ob->deleted) {
            $msg['status'] .= 'D';
        }
    }

    $msg['target'] = $target;
    $msgs[] = $msg;
}

$mailbox = Util::addParameter($mailbox_url, 'p', $pageOb->page);
$items = array($mailbox => _("Refresh"));

/* Determine if we are going to show the Purge Deleted link. */
if (!$prefs->getValue('use_trash') &&
    !$prefs->getValue('use_vtrash') &&
    !$imp_search->isVINBOXFolder()) {
    $items[Util::addParameter($mailbox, array('a' => 'e'))] = _("Purge Deleted");
}

/* Create sorting links. */
$sort = array();
$sort_list = array(
    SORTARRIVAL => '#',
    SORTFROM => _("From"),
    SORTSUBJECT => _("Subject")
);
foreach ($sort_list as $key => $val) {
    if ($sortpref['limit']) {
        $sort[$key] = (($key == SORTARRIVAL) ? '*' : '') . $val;
    } else {
        $sortdir = $sortpref['dir'];
        $sortkey = $key;
        if ($key == SORTSUBJECT &&
            !$GLOBALS['imp_search']->isSearchMbox($mailbox) &&
            (!$GLOBALS['prefs']->getValue('use_trash') ||
             !$GLOBALS['prefs']->getValue('use_vtrash') ||
             $GLOBALS['imp_search']->isVTrashFolder($mailbox))) {
            if ($sortpref['by'] != SORTTHREAD) {
                $items[Util::addParameter($mailbox, array('a' => 'c', 'sb' => SORTTHREAD, 'sd' => $sortdir))] = _("Sort by Thread");
            } else {
                $sortkey = SORTTHREAD;
                $items[Util::addParameter($mailbox, array('a' => 'c', 'sb' => SORTSUBJECT, 'sd' => $sortdir))] = _("Do Not Sort by Thread");
            }
        }
        if ($sortpref['by'] == $key) {
            $val = '*' . $val;
            $sortdir = !$sortdir;
        }
        $sort[$key] = new Horde_Mobile_link($val, Util::addParameter($mailbox, array('a' => 'c', 'sb' => $sortkey, 'sd' => $sortdir)));
    }
}

/* Create mailbox menu. */
$menu = new Horde_Mobile_card('o', _("Menu"));
$mset = &$menu->add(new Horde_Mobile_linkset());

foreach ($items as $link => $label) {
    $mset->add(new Horde_Mobile_link($label, $link));
}

$nav = array('pages_first', 'pages_prev', 'pages_next', 'pages_last');
foreach ($nav as $n) {
    if (Util::nonInputVar($n)) {
        $mset->add($$n);
    }
}

MIMP::addMIMPMenu($mset, 'mailbox');
require MIMP_TEMPLATES . '/mailbox/mailbox.inc';

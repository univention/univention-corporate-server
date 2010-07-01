<?php
/**
 * $Horde: mimp/folders.php,v 1.39.2.6 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Anil Madhavapeddy <avsm@horde.org>
 * @author Michael Slusarz <slusarz@horde.org>
 */

$load_imp = true;
@define('MIMP_BASE', dirname(__FILE__));
require_once MIMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/IMAP/Tree.php';

/* Redirect back to the mailbox if folder use is not allowed. */
if (empty($conf['user']['allow_folders'])) {
    header('Location: ' . Horde::url(MIMP_WEBROOT . 'mailbox.php', true));
    exit;
}

/* Decide whether or not to show all the unsubscribed folders */
$subscribe = $prefs->getValue('subscribe');
$showAll = (!$subscribe || $_SESSION['imp']['showunsub']);

/* Initialize the MIMP_Tree object. */
$imptree = &IMP_Tree::singleton();
$mask = IMPTREE_NEXT_SHOWCLOSED;

/* Toggle subscribed view, if necessary. */
if ($subscribe && Util::getFormData('ts')) {
    $showAll = !$showAll;
    $_SESSION['imp']['showunsub'] = $showAll;
    $imptree->showUnsubscribed($showAll);
    $mask |= IMPTREE_NEXT_SHOWSUB;
}

/* Start iterating through the list of mailboxes, displaying them. */
$rows = array();
$tree_ob = $imptree->build($mask);
foreach ($tree_ob[0] as $val) {
    $rows[] = array(
        'level' => str_repeat('..', $val['level']),
        'label' => $val['base_elt']['l'],
        'link' => ((empty($val['container'])) ? MIMP::generateMIMPUrl('mailbox.php', $val['value']) : null),
        'msgs' => ((isset($val['msgs'])) ? ($val['unseen'] . '/' . $val['msgs']) : null)
    );
}

$selfurl = Horde::url(MIMP_WEBROOT . 'folders.php');
if ($subscribe) {
    $sub_text = ($showAll) ? _("Show Subscribed Folders") : _("Show All Folders");
    $sub_link = Util::addParameter($selfurl, 'ts', 1);
}

$title = _("Folders");
require MIMP_TEMPLATES . '/folders/folders.inc';

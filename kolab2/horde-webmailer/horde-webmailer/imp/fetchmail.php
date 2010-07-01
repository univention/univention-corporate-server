<?php
/**
 * $Horde: imp/fetchmail.php,v 1.40.8.9 2009-01-06 15:24:01 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Nuno Loureiro <nuno@co.sapo.pt>
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('IMP_BASE', dirname(__FILE__));
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Fetchmail.php';
require_once IMP_BASE . '/lib/Template.php';
require_once 'Horde/Prefs/UI.php';

/* No fetchmail for POP3 accounts. */
if ($_SESSION['imp']['base_protocol'] == 'pop3') {
    echo _("Your account does not support fetching external mail.");
    exit;
}

/* Initialize Fetchmail libraries. */
$fm_account = new IMP_Fetchmail_Account();

/* Run through the action handlers. */
$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'fetchmail_fetch':
    $fetch_list = Util::getFormData('accounts');
    if (!empty($fetch_list)) {
        IMP_Fetchmail::fetchMail($fetch_list);

        /* Go to the download folder. */
        $lmailbox = $fm_account->getValue('lmailbox', $fetch_list[0]);
        $url = Util::addParameter(Horde::applicationUrl('mailbox.php'), 'mailbox', $lmailbox);
        if ($prefs->getValue('fetchmail_popup')) {
            Util::closeWindowJS('opener.focus();opener.location.href="' . $url . '";');
        } else {
            header('Location: ' . $url);
        }
        exit;
    }
    break;
}

$title = _("Fetch Mail");
require IMP_TEMPLATES . '/common-header.inc';

/* Prepare javascript variables. */
if (!$prefs->getValue('fetchmail_popup')) {
    IMP::menu();
}

/* Prepare template. */
$t = new IMP_Template();
$t->setOption('gettext', true);
$t->set('fetch_url', Horde::applicationUrl('fetchmail.php'));
$t->set('fetch_prefs', Horde::applicationUrl('fetchmailprefs.php'));
$t->set('forminput', Util::formInput());

$accounts = $fm_account->getAll('id');
if ($accounts) {
    $accountsval = array();
    foreach (array_keys($accounts) as $key) {
        $accountsval[] = array(
            'key' => $key,
            'label' => htmlspecialchars($fm_account->getValue('id', $key))
        );
    }
    $t->set('accounts', $accountsval);
}
if ($prefs->getValue('fetchmail_popup')) {
    $t->set('cancel_js', 'window.close();');
}

echo $t->fetch(IMP_TEMPLATES . '/fetchmail/fetchmail.html');
require $registry->get('templates', 'horde') . '/common-footer.inc';

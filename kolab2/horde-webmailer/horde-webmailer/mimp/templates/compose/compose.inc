<?php

$c = &$m->add(new Horde_Mobile_card('m', $title));
$c->softkey('#o', _("Menu"));

$l->setMobileObject($c);
$notification->notify(array('listeners' => 'status'));

$f = &$c->add(new Horde_Mobile_form('compose.php'));

// Hidden Variables.
$f->add(new Horde_Mobile_hidden('messageCache', $messageCacheID));
$f->add(new Horde_Mobile_hidden('thismailbox', Util::getFormData('thismailbox')));
$f->add(new Horde_Mobile_hidden('index', Util::getFormData('index')));

if (Util::getFormData('ctype')) {
    $f->add(new Horde_Mobile_hidden('ctype', Util::getFormData('ctype')));
} else {
    switch ($actionID) {
    case 'r':
    case 'ra':
    case 'rl':
        $f->add(new Horde_Mobile_hidden('ctype', 'reply'));
        break;

    case 'f':
        $f->add(new Horde_Mobile_hidden('ctype', 'forward'));
        break;
    }
}

if ((Util::getFormData('is_reply') == 1) || (strpos($actionID, 'reply') === 0)) {
    $f->add(new Horde_Mobile_hidden('is_reply', 1));
    $f->add(new Horde_Mobile_hidden('in_reply_to', $header['in_reply_to']));
    $f->add(new Horde_Mobile_hidden('references', $header['references']));
}

if (!$prefs->isLocked('default_identity')) {
    $ib = &$f->add(new Horde_Mobile_block(new Horde_Mobile_text(_("Identity"))));
    $ident_sel = &$ib->add(new Horde_Mobile_select('identity'));
    $default = Util::getFormData('identity', $identity->getDefault());
    foreach ($select_list as $key => $select) {
        $ident_sel->add($select, $key, ($key == $default));
    }
}

$f->add(new Horde_Mobile_input('to', $header['to'], _("To: ")));
if ($prefs->getValue('compose_cc')) {
    $f->add(new Horde_Mobile_input('cc', $header['cc'], _("Cc: ")));
}
if ($prefs->getValue('compose_bcc')) {
    $f->add(new Horde_Mobile_input('bcc', $header['bcc'], _("Bcc: ")));
}
$f->add(new Horde_Mobile_input('subject', $header['subject'], _("Subject: ")));

$f->add(new Horde_Mobile_textarea('message', $msg, _("Message: "), 10, 80));

$f->add(new Horde_Mobile_submit(_("Send"), 'a'));
$f->add(new Horde_Mobile_submit(_("Expand Names"), 'a'));

$m->add($menu);

$m->display();

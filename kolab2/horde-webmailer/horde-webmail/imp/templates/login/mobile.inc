<?php

$m = new Horde_Mobile(_("Log in"));

$c = &$m->add(new Horde_Mobile_card());

$notification = &new Notification();
$l = &$notification->attach('status', null, 'Notification_Listener_mobile');
$l->setMobileObject($c);

$c->add(new Horde_Mobile_text(sprintf(_("Welcome to %s"), ($imp_auth) ? $registry->get('name',' horde') : $registry->get('name'))));

$f = &$c->add(new Horde_Mobile_form(Horde::applicationUrl('redirect.php', false, -1)));
$f->add(new Horde_Mobile_input('imapuser', htmlspecialchars(Util::getFormData('imapuser')), _("Username: ")));

// Add a password input, and set the type accordingly.
$p = &$f->add(new Horde_Mobile_input('pass', '', _("Password: ")));
$p->set('type', 'password');

if (!empty($server_select)) {
    $f->add($server_select);
}

if (!empty($protocol_select)) {
    $f->add($protocol_select);
}

if (!empty($lang_select)) {
    $f->add($lang_select);
}

if (!empty($view_select)) {
    $f->add($view_select);
}

// Submit button.
$f->add(new Horde_Mobile_submit(_("Log in")));

if (!empty($actionID)) {
    $f->add(new Horde_Mobile_hidden('actionID', $actionID));
}
if (!empty($url_param)) {
    $f->add(new Horde_Mobile_hidden('url', $url_param));
}

// Add the form to the page.
$m->add($f);

// Display everything.
$m->display();

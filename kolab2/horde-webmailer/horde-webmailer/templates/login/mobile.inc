<?php

$m = &new Horde_Mobile(_("Log in"));
$m->add(new Horde_Mobile_text(sprintf(_("Welcome to %s"), $registry->get('name'))));

$f = &new Horde_Mobile_form('login.php');
$f->add(new Horde_Mobile_hidden('url', Util::getFormData('url', '')));
$f->add(new Horde_Mobile_input('horde_user', '', _("Username: ")));

// Add a password input, and set the type accordingly.
$p = &$f->add(new Horde_Mobile_input('horde_pass', '', _("Password: ")));
$p->set('type', 'password');

// Submit button.
$f->add(new Horde_Mobile_submit(_("Log in")));

// Add the form to the page.
$m->add($f);

// Display everything.
$m->display();

<?php

$c = &$m->add(new Horde_Mobile_card('m', $title));
$c->softkey('#o', _("Menu"));

$l->setMobileObject($c);
$notification->notify(array('listeners' => 'status'));

$f = &$c->add(new Horde_Mobile_form('compose.php'));

$f->add(new Horde_Mobile_hidden('thismailbox', $thismailbox));
$f->add(new Horde_Mobile_hidden('index', $index));
$f->add(new Horde_Mobile_hidden('action', 'rc'));
$f->add(new Horde_Mobile_hidden('array_index', Util::getFormData('array_index')));

$f->add(new Horde_Mobile_input('to', $header['to'], _("To: ")));

$f->add(new Horde_Mobile_submit(_("Redirect"), 'a'));
$f->add(new Horde_Mobile_submit(_("Expand Names"), 'a'));

$m->add($menu);

$m->display();

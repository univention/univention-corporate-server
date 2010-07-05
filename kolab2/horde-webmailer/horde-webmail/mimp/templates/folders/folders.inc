<?php
// $Horde

$m->set('title', $title);
$c = &$m->add(new Horde_Mobile_card('m', $title));
$c->softkey('#o', _("Menu"));
$l->setMobileObject($c);

$notification->notify(array('listeners' => 'status'));

$null = null;
$fb = &$c->add(new Horde_Mobile_block($null));

foreach ($rows as $val) {
    $fb->add(new Horde_Mobile_text($val['level']));
    if (empty($val['link'])) {
        $fb->add(new Horde_Mobile_text($val['label']));
    } else {
        $fb->add(new Horde_Mobile_link($val['label'], $val['link']));
    }
    if (!is_null($val['msgs'])) {
        $fb->add(new Horde_Mobile_text(' (' . $val['msgs'] . ')'));
    }

    $t = &$fb->add(new Horde_Mobile_text("\n"));
    $t->set('linebreaks', true);
}

$menu = &new Horde_Mobile_card('o', _("Menu"));
$mset = &$menu->add(new Horde_Mobile_linkset());
$mset->add(new Horde_Mobile_link(_("Refresh"), $selfurl));
if ($subscribe) {
    $mset->add(new Horde_Mobile_link($sub_text, $sub_link));
}
MIMP::addMIMPMenu($mset, 'folders');
$m->add($menu);

$m->display();

<?php

if (!empty($msgcount)) {
    $title .= ' (' . $unseen . '/' .  $msgcount . ')';
}
if ($pageOb->pagecount > 1) {
    $title .= ' - ' . $pageOb->page . ' ' . _("of") . ' ' . $pageOb->pagecount;
}
$c = &$m->add(new Horde_Mobile_card('m', $title));
$c->softkey('#o', _("Menu"));

$GLOBALS['l']->setMobileObject($c);
$GLOBALS['notification']->notify(array('listeners' => 'status'));

if (!empty($pageOb->end)) {
    $t = &$c->add(new Horde_Mobile_table());
    $t->set('border', 0);
    $t->set('padding', 1);
    $t->set('spacing', 1);

    $r = &$t->add(new Horde_Mobile_row());
    $r->add($sort[SORTARRIVAL]);
    $r->add($sort[SORTFROM]);
    $r->add($sort[SORTSUBJECT]);

    $i = 1;
    foreach ($msgs as $msg) {
        $r = &$t->add(new Horde_Mobile_row());
        $r->add($msg['status']);
        $r->add($msg['from']);
        $l = &$r->add(new Horde_Mobile_link($msg['subject'], $msg['target']));
        $l->set('accesskey', $i++);
    }
}

$m->add($menu);
$m->display();

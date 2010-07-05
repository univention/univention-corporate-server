<?php
/**
 * URL Parameters:
 * ---------------
 * 'search_mailbox'  --  If exists, don't show the folder selection list; use
 *                       the passed in mailbox value instead.
 * 'edit_query'      --  If exists, the search query to edit.
 *
 * $Horde: imp/search.php,v 2.128.2.34 2009-01-06 15:24:02 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('IMP_BASE', dirname(__FILE__));
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Template.php';
require_once 'Horde/Help.php';

$actionID = Util::getFormData('actionID');
$edit_query = Util::getFormData('edit_query');
$edit_query_vfolder = Util::getFormData('edit_query_vfolder');
$search_mailbox = Util::getFormData('search_mailbox');

$imp_search_fields = $imp_search->searchFields();

/* Get URL parameter data. */
$search = array();
if (Util::getFormData('no_match')) {
    $search = $imp_search->retrieveUIQuery();
    $retrieve_search = true;
} elseif (($edit_query !== null) && $imp_search->isSearchMbox($edit_query)) {
    if ($imp_search->isVFolder($edit_query)) {
        if (!$imp_search->isEditableVFolder($edit_query)) {
            $notification->push(_("Special Virtual Folders cannot be edited."), 'horde.error');
            header('Location: ' . Horde::applicationUrl('mailbox.php', true));
            exit;
        }
        $edit_query_vfolder = $edit_query;
    }
    $search = $imp_search->retrieveUIQuery($edit_query);
    $retrieve_search = true;
} else {
    $retrieve_search = false;
}
if (empty($search)) {
    $search['field'] = Util::getFormData('field', array('from', 'to', 'subject', 'body'));
    if (!empty($search['field']) && !end($search['field'])) {
        array_pop($search['field']);
    }
    $search['field_end'] = count($search['field']);
    $search['match'] = Util::getFormData('search_match');
    $search['text'] = Util::getFormData('search_text');
    $search['text_not'] = Util::getFormData('search_text_not');
    $search['date'] = Util::getFormData('search_date');
    $search['folders'] = Util::getFormData('search_folders', array());
    $search['save_vfolder'] = Util::getFormData('save_vfolder');
    $search['vfolder_label'] = Util::getFormData('vfolder_label');
    $search['mbox'] = Util::getFormData('mbox', $search_mailbox);
}

/* Run through the action handlers. */
switch ($actionID) {
case 'do_search':
    /* Need to convert size from KB to bytes. */
    for ($i = 0; $i <= $search['field_end']; $i++) {
        if (isset($search['field'][$i]) &&
            isset($imp_search_fields[$search['field'][$i]]) &&
            ($imp_search_fields[$search['field'][$i]]['type'] == IMP_SEARCH_SIZE)) {
            $search['text'][$i] *= 1024;
        }
    }

    /* Create the search query. */
    $query = $imp_search->createQuery($search);

    /* Save the search as a virtual folder if requested. */
    if (!empty($search['save_vfolder'])) {
        if (empty($search['vfolder_label'])) {
            $notification->push(_("Virtual Folders require a label."), 'horde.error');
            break;
        }

        $id = $imp_search->addVFolder($query, $search['folders'], $search, $search['vfolder_label'], (empty($edit_query_vfolder) ? null : $edit_query_vfolder));
        $notification->push(sprintf(_("Virtual Folder \"%s\" created succesfully."), $search['vfolder_label']), 'horde.success');
    } else {
        /* Set the search in the IMP session. */
        $id = $imp_search->createSearchQuery($query, $search['folders'], $search, _("Search Results"));
    }

    /* Redirect to the Mailbox Screen. */
    header('Location: ' . Util::addParameter(Horde::applicationUrl('mailbox.php', true), 'mailbox', $GLOBALS['imp_search']->createSearchID($id), false));
    exit;

case 'reset_search':
    if ($def_search = $prefs->getValue('default_search')) {
        $search['field'] = array($def_search);
        $search['field_end'] = 1;
    } else {
        $search['field'] = array();
        $search['field_end'] = 0;
    }
    $search['match'] = null;
    $search['date'] = $search['text'] = $search['text_not'] = $search['flag'] = array();
    $search['folders'] = array();
    break;

case 'delete_field':
    $key = Util::getFormData('delete_field_id');

    /* Unset all entries in array input and readjust ids. */
    $vars = array('field', 'text', 'text_not', 'date');
    foreach ($vars as $val) {
        unset($search[$val][$key]);
        if (!empty($search[$val])) {
            $search[$val] = array_values($search[$val]);
        }
    }
    $search['field_end'] = count($search['field']);
    break;
}

$shown = null;
if (!$conf['user']['allow_folders']) {
    $search['mbox'] = 'INBOX';
    $search['folders'][] = 'INBOX';
    $subscribe = false;
} elseif ($subscribe = $prefs->getValue('subscribe')) {
    $shown = Util::getFormData('show_subscribed_only', $subscribe);
}

/* Prepare the search template. */
$t = new IMP_Template();
$t->setOption('gettext', true);

$t->set('action', Horde::applicationUrl('search.php'));
$t->set('subscribe', $subscribe);
$t->set('shown', htmlspecialchars($shown));
$t->set('edit_query_vfolder', htmlspecialchars($edit_query_vfolder));
if (!$edit_query_vfolder) {
    if (empty($search['mbox'])) {
        $t->set('search_title', _("Search"));
    } else {
        $t->set('search_title',
                sprintf(
                    _("Search %s"),
                    Horde::link(
                        Horde::url(Util::addParameter('mailbox.php',
                                                      'mailbox',
                                                      $search['mbox'])))
                    . htmlspecialchars(IMP::displayFolder($search['mbox']))
                    . '</a>'));
    }
}
$t->set('search_help', Help::link('imp', 'search'));
$t->set('field_end', $search['field_end'] > 0);
$t->set('match_or', $search['match'] == 'or');
$t->set('label_or', Horde::label('search_match_or', _("Match Any Query")));
$t->set('match_and', ($search['match'] == null) || ($search['match'] == 'and'));
$t->set('label_and', Horde::label('search_match_and', _("Match All Queries")));

$saved_searches = $imp_search->getSearchQueries();
if (!empty($saved_searches)) {
    $ss = array();
    foreach ($saved_searches as $key => $val) {
        if (String::length($val) > 100) {
            $val = String::substr($val, 0, 100) . ' ...';
        }
        $ss[] = array('val' => htmlspecialchars($key), 'text' => htmlspecialchars($val));
    }
    $t->set('saved_searches', $ss);
}

$fields = $f_fields = $s_fields = array();
$js_first = 0;

/* Process the list of fields. */
foreach ($imp_search_fields as $key => $val) {
    $s_fields[$key] = array(
        'val' => $key,
        'label' => $val['label'],
        'sel' => null
    );
}
foreach ($imp_search->flagFields() as $key => $val) {
    $f_fields[$key] = array(
        'val' => $key,
        'label' => $val['label'],
        'sel' => null
    );
}

for ($i = 0; $i <= $search['field_end']; $i++) {
    $curr = (isset($search['field'][$i])) ? $search['field'][$i] : null;
    $fields[$i] = array(
        'i' => $i,
        'last' => ($i == $search['field_end']),
        'curr' => $curr,
        'f_fields' => $f_fields,
        'first' => (($i == 0) && ($i != $search['field_end'])),
        'notfirst' => ($i > 0),
        's_fields' => $s_fields,
        'search_text' => false,
        'search_date' => false,
        'js_calendar' => null
    );
    if ($curr !== null) {
        if (isset($f_fields[$curr])) {
            $fields[$i]['f_fields'][$curr]['sel'] = true;
        } else {
            $fields[$i]['s_fields'][$curr]['sel'] = true;
            if (in_array($imp_search_fields[$curr]['type'], array(IMP_SEARCH_HEADER, IMP_SEARCH_BODY, IMP_SEARCH_TEXT, IMP_SEARCH_SIZE))) {
                $fields[$i]['search_text'] = true;
                $fields[$i]['search_text_val'] = (!empty($search['text'][$i])) ? @htmlspecialchars($search['text'][$i], ENT_COMPAT, NLS::getCharset()) : null;
                if ($retrieve_search &&
                    ($imp_search_fields[$curr]['type'] == IMP_SEARCH_SIZE)) {
                    $fields[$i]['search_text_val'] /= 1024;
                }
                if ($imp_search_fields[$curr]['not']) {
                    $fields[$i]['show_not'] = true;
                    $fields[$i]['search_text_not'] = (!empty($search['text_not'][$i]));
                }
            } elseif ($imp_search_fields[$curr]['type'] == IMP_SEARCH_DATE) {
                if (!isset($curr_date)) {
                    $curr_date = getdate();
                }
                $fields[$i]['search_date'] = true;

                $fields[$i]['month'] = array();
                $month_default = isset($search['date'][$i]['month']) ? $search['date'][$i]['month'] : $curr_date['mon'];
                for ($month = 1; $month <= 12; $month++) {
                    $fields[$i]['month'][] = array(
                        'val' => $month,
                        'sel' => ($month == $month_default),
                        'label' => strftime('%B', mktime(0, 0, 0, $month, 1))
                    );
                }

                $fields[$i]['day'] = array();
                $day_default = isset($search['date'][$i]['day']) ? $search['date'][$i]['day'] : $curr_date['mday'];
                for ($day = 1; $day <= 31; $day++) {
                    $fields[$i]['day'][] = array(
                        'val' => $day,
                        'sel' => ($day == $day_default)
                    );
                }

                $fields[$i]['year'] = array();
                $year_default = isset($search['date'][$i]['year']) ? $search['date'][$i]['year'] : $curr_date['year'];
                if (!isset($curr_year)) {
                    $curr_year = date('Y');
                    $yearlist = array();
                    $years = -20;
                    $startyear = (($year_default < $curr_year) && ($years > 0)) ? $year_default : $curr_year;
                    $startyear = min($startyear, $startyear + $years);
                    for ($j = 0; $j <= abs($years); $j++) {
                        $yearlist[] = $startyear++;
                    }
                    if ($years < 0) {
                        $yearlist = array_reverse($yearlist);
                    }
                }
                foreach ($yearlist as $year) {
                    $fields[$i]['year'][] = array(
                        'val' => $year,
                        'sel' => ($year == $year_default)
                    );
                }

                if ($browser->hasFeature('javascript')) {
                    Horde::addScriptFile('open_calendar.js', 'horde');
                    $fields[$i]['js_calendar_first'] = !$js_first++;
                    $fields[$i]['js_calendar'] = Horde::link('#', _("Select a date"), '', '', 'openCalendar(\'dateimg' . $i . '\', \'search_date_' . $i . '\'); return false;');
                    $fields[$i]['js_calendar_img'] = Horde::img('calendar.png', _("Calendar"), 'align="top" id="dateimg' . $i . '"', $GLOBALS['registry']->getImageDir('horde'));
                }
            }
        }
    }
}
$t->set('fields', array_values($fields));
$t->set('delete_img', $registry->getImageDir('horde') . '/delete.png');
$t->set('remove', _("Remove Field From Search"));

if ($subscribe) {
    $t->set('inverse_subscribe', ($shown == IMP_SEARCH_SHOW_UNSUBSCRIBED) ? IMP_SEARCH_SHOW_SUBSCRIBED_ONLY : IMP_SEARCH_SHOW_UNSUBSCRIBED);
}

$t->set('mbox', htmlspecialchars($search['mbox']));
$t->set('virtualfolder', $_SESSION['imp']['base_protocol'] != 'pop3');
if ($t->get('virtualfolder')) {
    $t->set('save_vfolder', !empty($search['save_vfolder']));
    $t->set('vfolder_label', !empty($search['vfolder_label']) ? htmlspecialchars($search['vfolder_label'], ENT_COMPAT, NLS::getCharset()) : null);
}

if (empty($search['mbox'])) {
    $count = -1;
    $mboxes = array();
    $newcol = $numcolumns = 1;

    require_once IMP_BASE . '/lib/Folder.php';
    $imp_folder = &IMP_Folder::singleton();
    $mailboxes = $imp_folder->flist_IMP(array(), ($shown !== null) ? $shown : null);
    $total = ceil(count($mailboxes) / 3);

    if (empty($search['folders']) && ($actionID != 'update_search')) {
        /* Default to Inbox search. */
        $search['folders'][] = 'INBOX';
    }

    foreach ($mailboxes as $key => $mbox) {
        $mboxes[$key] = array(
            'count' => ++$count,
            'val' => (!empty($mbox['val']) ? htmlspecialchars($mbox['val']) : null),
            'sel' => false,
            'label' => str_replace(' ', '&nbsp;', $mbox['label']),
            'newcol' => false
        );

        if (!empty($mbox['val']) &&
            in_array($mbox['val'], $search['folders'])) {
            $mboxes[$key]['sel'] = true;
        }

        if ((++$newcol > $total) && ($numcolumns != 3)) {
            $newcol = 1;
            ++$numcolumns;
            $mboxes[$key]['newcol'] = true;
        }
    }
    $t->set('mboxes', array_values($mboxes));
}

$title = _("Message Search");
Horde::addScriptFile('stripe.js', 'imp', true);
Horde::addScriptFile('prototype.js', 'imp', true);
Horde::addScriptFile('search.js', 'imp', true);
require IMP_TEMPLATES . '/common-header.inc';
IMP::menu();
IMP::status();
IMP::addInlineScript(array(
    'var search_month = \'' . date('m') . '\'',
    'var search_day = \'' . date('d') . '\'',
    'var search_year = \'' . date('Y') . '\'',
    'var not_search = ' . intval(empty($search['mbox'])),
));
echo $t->fetch(IMP_TEMPLATES . '/search/search.html');
require $registry->get('templates', 'horde') . '/common-footer.inc';

<?php
/**
 * $Horde: mnemo/list.php,v 1.35.8.11 2009-01-06 15:24:57 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('MNEMO_BASE', dirname(__FILE__));
require_once MNEMO_BASE . '/lib/base.php';
require_once 'Horde/Prefs/CategoryManager.php';

/* Get the current action ID. */
$actionID = Util::getFormData('actionID');

/* Sort out the sorting values. */
if (Util::getFormData('sortby') !== null) {
    $prefs->setValue('sortby', Util::getFormData('sortby'));
}
if (Util::getFormData('sortdir') !== null) {
   $prefs->setValue('sortdir', Util::getFormData('sortdir'));
}

/* Get the full, sorted notepad. */
$memos = Mnemo::listMemos($prefs->getValue('sortby'),
                          $prefs->getValue('sortdir'));

/* Page variables. */
$title = _("My Notes");

switch ($actionID) {
case 'search_memos':
    /* If we're searching, only list those notes that match the search
     * result. */
    $search_pattern = Util::getFormData('search_pattern');
    $search_type = Util::getFormData('search_type');
    $search_desc = ($search_type == 'desc');
    $search_body = ($search_type == 'body');

    if (!empty($search_pattern) && ($search_body || $search_desc)) {
        $search_pattern = '/' . preg_quote($search_pattern, '/') . '/i';
        $search_result = array();
        foreach ($memos as $memo_id => $memo) {
            if (($search_desc && preg_match($search_pattern, $memo['desc'])) ||
                ($search_body && preg_match($search_pattern, $memo['body']))) {
                $search_result[$memo_id] = $memo;
            }
        }

        /* Reassign $memos to the search result. */
        $memos = $search_result;
        $title = _("Search Results");
    }
    break;
}

Horde::addScriptFile('tooltip.js', 'horde', true);
Horde::addScriptFile('tables.js', 'mnemo', true);
Horde::addScriptFile('prototype.js', 'mnemo', true);
Horde::addScriptFile('QuickFinder.js', 'mnemo', true);
require MNEMO_TEMPLATES . '/common-header.inc';
require MNEMO_TEMPLATES . '/menu.inc';
require MNEMO_TEMPLATES . '/list/header.inc';

if (count($memos)) {
    $cManager = new Prefs_CategoryManager();
    $colors = $cManager->colors();
    $fgcolors = $cManager->fgColors();
    $sortby = $prefs->getValue('sortby');
    $sortdir = $prefs->getValue('sortdir');
    $showNotepad = $prefs->getValue('show_notepad');

    $baseurl = 'list.php';
    if ($actionID == 'search_memos') {
        $baseurl = Util::addParameter(
            $baseurl,
            array('actionID' => 'search_memos',
                  'search_pattern' => $search_pattern,
                  'search_type' => $search_type));
    }

    require MNEMO_TEMPLATES . '/list/memo_headers.inc';

    foreach ($memos as $memo_id => $memo) {
        $viewurl = Util::addParameter(
            'view.php',
            array('memo' => $memo['memo_id'],
                  'memolist' => $memo['memolist_id']));

        $memourl = Util::addParameter(
            'memo.php', array('memo' => $memo['memo_id'],
                              'memolist' => $memo['memolist_id']));
        $share = &$GLOBALS['mnemo_shares']->getShare($memo['memolist_id']);

        $notepad = $memo['memolist_id'];
        if (!is_a($share, 'PEAR_Error')) {
            $notepad = $share->get('name');
        }

        require MNEMO_TEMPLATES . '/list/memo_summaries.inc';
    }

    require MNEMO_TEMPLATES . '/list/memo_footers.inc';
} else {
    require MNEMO_TEMPLATES . '/list/empty.inc';
}

require MNEMO_TEMPLATES . '/panel.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';

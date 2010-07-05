<?php
/**
 * $Horde: dimp/message.php,v 1.52.2.17 2009-01-06 15:22:37 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

$load_imp = true;
@define('DIMP_BASE', dirname(__FILE__));
require_once DIMP_BASE . '/lib/base.php';

$folder = Util::getFormData('folder');
$index = Util::getFormData('uid');
if (!$index || !$folder) {
    exit;
}

require_once IMP_BASE . '/lib/UI/Message.php';
$imp_ui = new IMP_UI_Message();

$args = array(
    'headers' => array_diff(array_keys($imp_ui->basicHeaders()), array('subject')),
    'folder' => $folder,
    'index' => $index,
    'preview' => false,
);

require_once DIMP_BASE . '/lib/Views/ShowMessage.php';
$show_msg = new DIMP_Views_ShowMessage();
$show_msg_result = $show_msg->ShowMessage($args);
if (isset($show_msg_result['error'])) {
    echo IMP::wrapInlineScript(array(
        DIMP::notify(false, 'parent.opener.document', 'parent.opener.DimpCore'),
        'parent.close()'
    ));
    exit;
}

$compose_args = array(
    'folder' => $folder,
    'index' => $index,
    'messageCache' => '',
    'popup' => false,
    'qreply' => true,
);
require_once DIMP_BASE . '/lib/Views/Compose.php';
$compose_view = new DIMP_Views_Compose;
$compose_result = $compose_view->showCompose($compose_args);

/* Need the Header object to check for list information. */
$msg_cache = &IMP_MessageCache::singleton();
$cache_entry = $msg_cache->retrieve($folder, array($index), 32);
$ob = reset($cache_entry);

/* Init IMP_UI_Compose:: object. */
require_once IMP_BASE . '/lib/UI/Compose.php';
$imp_ui = new IMP_UI_Compose();

/* Attach spellchecker & auto completer. */
require_once DIMP_BASE . '/lib/Dimple.php';
$imp_ui->attachAutoCompleter('Dimple', array('to', 'cc', 'bcc'));
$imp_ui->attachSpellChecker('dimp');

$compose_result['js'] = array_merge($compose_result['js'], array(
    'DIMP.conf.msg_index = "' . $show_msg_result['index'] . '"',
    'DIMP.conf.msg_folder = "' . $show_msg_result['folder'] . '"',
    'DIMP.conf.msg_source_link = "' . (isset($show_msg_result['source_link']) ? $show_msg_result['source_link'] : '') . '"'
));
IMP::addInlineScript($compose_result['js']);
IMP::addInlineScript($compose_result['jsonload'], 'load');
IMP::addInlineScript(array(DIMP::notify()), 'dom');

$scripts = array(
    array('ContextSensitive.js', 'dimp', true),
    array('fullmessage.js', 'dimp', true),
    array('compose.js', 'dimp', true),
    array('unblockImages.js', 'imp', true)
);

DIMP::header($show_msg_result['subject'], $scripts);
echo "<body>\n";
require DIMP_TEMPLATES . '/chunks/message.php';
DIMP::outputJS();
echo $compose_result['jsappend'];
$notification->notify(array('listeners' => array('javascript')));
echo "</body>\n</html>";

<?php
/**
 * $Horde: turba/minisearch.php,v 1.12 2004/02/25 21:21:37 chuck Exp $
 *
 * Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Source.php';
require TURBA_BASE . '/config/attributes.php';

$search = Util::getFormData('search');
$results = array();

// Make sure we have a source
$source = Util::getFormData('source');
if (!isset($source) && isset($cfgSources) && is_array($cfgSources) && count($cfgSources) > 0) {
    $source = $prefs->getValue('default_dir');
}
if (!isset($cfgSources[$source])) {
    reset($cfgSources);
    $source = key($cfgSources);
}

// Do the search if we have one
if (!is_null($search)) {
    $driver = &Turba_Source::singleton($source, $cfgSources[$source]);
    if (!is_a($driver, 'PEAR_Error')) {
        $criteria['name'] = trim($search);
        $res = $driver->search($criteria, 'lastname', 'OR');
        if (is_a($res, 'Turba_List')) {
            while ($ob = $res->next()) {
                if ($ob->isGroup()) {
                    continue;
                }
                $att = $ob->getAttributes();
                foreach ($att as $key => $value) {
                    if (!empty($attributes[$key]['type']) && $attributes[$key]['type'] == 'email') {
                        $results[] = array('name' => $att['name'],
                                           'email' => $value,
                                           'source' => $source,
                                           'key' => $att['__key']
                                           );
                        break;
                    }
                }
            }
        }
    }
}

$bodyClass = 'summary';
require TURBA_TEMPLATES . '/common-header.inc';

?>
<script language="JavaScript" type="text/javascript">
<!--
window.setTimeout('var status = window.parent.document.getElementById(\'turba_minisearch_searching\'); status.style.visibility = \'hidden\'', 10);
window.parent.busyExpanding = false;
//--//-->
</script>
<?php
if (count($results)) {
    echo '<table border="0" width="100%"><tr><td class="control"><b>' . _("Search Results") . ':</b></td></tr>';

    $i = 0;
    foreach ($results as $contact) {
        $url = 'display.php';
        $url = Util::addParameter($url, 'source', $contact['source']);
        $url = Util::addParameter($url, 'key', $contact['key']);

        echo '<tr><td class="item' . ($i++ % 2) . '">';
        echo Horde::link(Horde::applicationUrl($url), _("View Contact"), '', '_parent') . Horde::img('turba.gif', _("View Contact")) . "</a> &nbsp;";

        $mail_link = $GLOBALS['registry']->call('mail/compose', array(array('to' => addslashes($contact['email']))));
        if (is_a($mail_link, 'PEAR_Error')) {
            $mail_link = 'mailto:' . urlencode($contact['email']);
        }

        echo '<a href="' . $mail_link . '" target="_parent">' . htmlspecialchars($contact['name'] . " <" . $contact['email'] . ">") . '</a></td></tr>';
    }
    echo '</table>';
} elseif (!is_null($search)) {
    echo _("No contacts found");
}
?>
</body>
</html>

<?php
/**
 * $Horde: turba/minisearch.php,v 1.20.4.16 2009-01-06 15:27:39 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';

$search = Util::getFormData('search');
$results = array();

// Make sure we have a source.
$source = Util::getFormData('source', Turba::getDefaultAddressBook());

// Do the search if we have one.
if (!is_null($search)) {
    $driver = &Turba_Driver::singleton($source);
    if (!is_a($driver, 'PEAR_Error')) {
        $criteria['name'] = trim($search);
        $res = $driver->search($criteria);
        if (is_a($res, 'Turba_List')) {
            while ($ob = $res->next()) {
                if ($ob->isGroup()) {
                    continue;
                }
                $att = $ob->getAttributes();
                foreach ($att as $key => $value) {
                    if (!empty($attributes[$key]['type']) &&
                        $attributes[$key]['type'] == 'email') {
                        $results[] = array('name' => $ob->getValue('name'),
                                           'email' => $value,
                                           'url' => $ob->url());
                        break;
                    }
                }
            }
        }
    }
}

Horde::addScriptFile('prototype.js', 'turba', true);
$bodyClass = 'summary';
require TURBA_TEMPLATES . '/common-header.inc';

?>
<?php
if (count($results)) {
    echo '<ul id="turba_minisearch_results">';
    foreach ($results as $contact) {
        echo '<li class="linedRow">';

        $mail_link = $GLOBALS['registry']->call(
            'mail/compose',
            array(array('to' => addslashes($contact['email']))));
        if (is_a($mail_link, 'PEAR_Error')) {
            $mail_link = 'mailto:' . urlencode($contact['email']);
            $target = '';
        } else {
            $target = strpos($mail_link, 'javascript:') === 0
                ? ''
                : ' target="_parent"';
        }

        echo Horde::link(Horde::applicationUrl($contact['url']),
                        _("View Contact"), '', '_parent')
            . Horde::img('contact.png', _("View Contact")) . '</a> '
            . '<a href="' . $mail_link . '"' . $target . '>'
            . htmlspecialchars($contact['name'] . ' <' . $contact['email'] . '>')
            . '</a></li>';
    }
    echo '</ul>';
} elseif (!is_null($search)) {
    echo _("No contacts found");
}
?>
<script type="text/javascript">
var status = parent.$('turba_minisearch_searching');
if (status) {
    status.hide();
}
var iframe = parent.$('turba_minisearch_iframe');
if (iframe) {
    iframe.setStyle({
        height: Math.min($('turba_minisearch_results').getHeight(), 150) + 'px'
    });
}
parent.busyExpanding = false;
</script>
</body>
</html>

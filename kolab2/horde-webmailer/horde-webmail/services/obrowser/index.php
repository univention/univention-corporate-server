<?php
/**
 * $Horde: horde/services/obrowser/index.php,v 1.6.10.10 2009-01-06 15:27:30 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Template.php';

$path = Util::getFormData('path');

if (empty($path)) {
    $list = array();
    $apps = $registry->listApps(null, false, PERMS_READ);
    foreach ($apps as $app) {
        if ($registry->hasMethod('browse', $app)) {
            $list[$app] = array('name' => $registry->get('name', $app),
                                'icon' => $registry->get('icon', $app),
                                'browseable' => true);
        }
    }
} else {
    $pieces = explode('/', $path);
    $list = $registry->callByPackage($pieces[0], 'browse', array('path' => $path));
}

if (is_a($list, 'PEAR_Error')) {
    Horde::fatal($list, __FILE__, __LINE__);
}
if (!count($list)) {
    Horde::fatal(_("Nothing to browse, go back."), __FILE__, __LINE__);
}

$tpl = <<<TPL
<script type="text/javascript">
function chooseObject(oid)
{
    if (!window.opener || !window.opener.obrowserCallback) {
        return false;
    }

    var result = window.opener.obrowserCallback(window.name, oid);
    if (!result) {
        window.close();
        return;
    }

    alert(result);
    return false;
}
</script>

<div class="header">
 <span class="rightFloat"><tag:close /></span>
 <gettext>Object Browser</gettext>
</div>
<div class="headerbox">
 <table class="striped" cellspacing="0" style="width:100%">
 <loop:rows>
  <tr>
   <td>
    <tag:rows.icon />
    <tag:rows.name />
   </td>
  </tr>
 </loop:rows>
 </table>
</div>
TPL;

$rows = array();
foreach ($list as $path => $values) {
    $row = array();

    // Set the icon.
    if (!empty($values['icon'])) {
        $row['icon'] = Horde::img($values['icon'], $values['name'], '', '');
    } elseif (!empty($values['browseable'])) {
        $row['icon'] = Horde::img('tree/folder.png');
    } else {
        $row['icon'] = Horde::img('tree/leaf.png');
    }

    // Set the name/link.
    if (!empty($values['browseable'])) {
        $url = Horde::url($registry->get('webroot', 'horde') . '/services/obrowser/');
        $url = Util::addParameter($url, 'path', $path);
        $row['name'] = Horde::link($url) . htmlspecialchars($values['name']) . '</a>';
    } else {
        $js = "return chooseObject('" . addslashes($path) . "');";
        $row['name'] = Horde::link('#', sprintf(_("Choose %s"), $values['name']), '', '', $js) . htmlspecialchars($values['name']) . '</a>';
    }

    $rows[] = $row;
}

$template = new Horde_Template();
$template->setOption('gettext', true);
$template->set('rows', $rows);
$template->set('close', '<a href="#" onclick="window.close(); return false;">' . Horde::img('close.png') . '</a>');

Horde::addScriptFile('stripe.js', 'horde', true);
require HORDE_TEMPLATES . '/common-header.inc';
echo $template->parse($tpl);
require HORDE_TEMPLATES . '/common-footer.inc';

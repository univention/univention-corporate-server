<?php
/**
 * $Horde: horde/admin/phpshell.php,v 1.24.10.15 2009-10-13 15:52:07 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

$title = _("PHP Shell");
Horde::addScriptFile('stripe.js', 'horde', true);
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/menu.inc';

$apps_tmp = $registry->listApps();
$apps = array();
foreach ($apps_tmp as $app) {
    // Make sure the app is installed.
    if (!file_exists($registry->get('fileroot', $app))) {
        continue;
    }

    $apps[$app] = $registry->get('name', $app) . ' (' . $app . ')';
}
asort($apps);
$application = Util::getFormData('app', 'horde');

$command = trim(Util::getFormData('php'))

?>
<div style="padding:10px">
<form action="phpshell.php" method="post">
<?php Util::pformInput() ?>

<h1 class="header"><?php echo _("PHP Shell") ?></h1>
<br />
<label for="app"><?php echo _("Application Context: ") ?></label>
<select id="app" name="app">
<?php foreach ($apps as $app => $name): ?>
 <option value="<?php echo $app ?>"<?php if ($application == $app) echo ' selected="selected"' ?>><?php echo $name ?></option>
<?php endforeach; ?>
</select><br /><br />

<label for="php" class="hidden"><?php echo _("PHP") ?></label>
<textarea class="fixed" id="php" name="php" rows="10" style="width:100%; padding:0;">
<?php if (!empty($command)) echo htmlspecialchars($command) ?></textarea>
<br />
<input type="submit" class="button" value="<?php echo _("Execute") ?>" />
<?php echo Help::link('admin', 'admin-phpshell') ?>
</form><br />

<?php

if ($command) {
    if (file_exists($registry->get('fileroot', $application) . '/lib/base.php')) {
        include $registry->get('fileroot', $application) . '/lib/base.php';
    } else {
        $registry->pushApp($application);
    }

    require_once 'Horde/MIME/Viewer.php';
    require_once 'Horde/MIME/Viewer/php.php';
    $viewer = new MIME_Viewer_php($null);

    ini_set('highlight.comment', 'comment');
    ini_set('highlight.default', 'default');
    ini_set('highlight.keyword', 'keyword');
    ini_set('highlight.string', 'string');
    ini_set('highlight.html', 'html');
    $pretty = $viewer->lineNumber(str_replace('&lt;?php&nbsp;', '', highlight_string('<?php ' . $command, true)));

    echo '<h1 class="header">' . _("PHP Code") . '</h1>';
    echo $pretty;
    echo '<br />';

    echo '<h1 class="header">' . _("Results") . '</h1>';
    echo '<pre class="text">';
    eval($command);
    echo '</pre>';
}
?>

</div>
<?php

require HORDE_TEMPLATES . '/common-footer.inc';

<?php
/**
 * $Horde: horde/admin/phpshell.php,v 1.22 2004/04/29 19:14:08 jan Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Help.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

$title = _("PHP Shell");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';

$apps = $registry->listApps();
$application = Util::getFormData('app', 'horde');
?>
<form action="<?php echo $_SERVER['PHP_SELF'] ?>" method="post">
<?php Util::pformInput() ?>

<table width="100%" border="0" cellpadding="2" cellspacing="0"><tr><td class="header"><?php echo _("Application") ?></td></tr></table>
<select name="app">
<?php foreach ($apps as $app): ?>
  <option value="<?php echo $app ?>"<?php if ($application == $app) echo ' selected="selected"' ?>><?php echo $registry->getParam('name', $app) ?></option>
<?php endforeach; ?>
</select><br /><br />
<?php

if ($command = trim(Util::getFormData('php'))) {
    if (@file_exists($registry->getParam('fileroot', $application) . '/lib/base.php')) {
        include $registry->getParam('fileroot', $application) . '/lib/base.php';
    } else {
        $registry->pushApp($application);
    }

    require_once 'Horde/MIME/Viewer.php';
    require_once 'Horde/MIME/Viewer/source.php';
    $pretty = highlight_string('<?php ' . $command . "\n", true);
    $pretty = str_replace(array('&lt;?php',
                                "\r\n",
                                "\r",
                                "<code><font color=\"#000000\">\n",
                                "\n</code>",
                                "\n</font></code>"),
                          array('',
                                "\n",
                                "\n",
                                '<code><font color="#000000">',
                                '</code>',
                                '</font></code>'),
                          $pretty);
    $pretty = MIME_Viewer_Source::lineNumber(trim($pretty));

    echo '<table width="100%" border="0" cellpadding="2" cellspacing="0"><tr><td class="header">' . _("PHP Code") . '</td></tr></table><br />';
    echo $pretty;

    echo '<br /><table width="100%" border="0" cellpadding="2" cellspacing="0"><tr><td class="header">' . _("Results") . '</td></tr></table>';
    echo '<table cellpadding="4" border="0"><tr><td class="text"><pre>';
    eval($command);
    echo '</pre></td></tr></table><br />';
}
?>

<textarea class="fixed" name="php" rows="10" cols="60">
<?php if (!empty($command)) echo htmlspecialchars($command) ?></textarea>
<br />
<input type="submit" class="button" value="<?php echo _("Execute") ?>">
<?php if ($conf['user']['online_help'] && $browser->hasFeature('javascript')): ?>
    <?php Help::javascript(); ?>
    <td class="header" align="right"><?php echo Help::link('admin', 'admin-phpshell') ?></td>
<?php endif; ?>

</form>
<?php

require HORDE_TEMPLATES . '/common-footer.inc';

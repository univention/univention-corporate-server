<?php
/**
 * $Horde: horde/admin/cmdshell.php,v 1.8 2004/04/07 14:43:01 chuck Exp $
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
    Horde::fatal('Forbidden.', __FILE__, __LINE__);
}

$title = _("Command Shell");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';

if ($command = trim(Util::getFormData('cmd'))) {
    echo '<div class="header">' . _("Command") . ':</div><br />';
    echo '<table cellpadding="4" border="0"><tr><td class="text"><code>' . nl2br(htmlspecialchars($command)) . '</code></td></tr></table>';

    echo '<br /><div class="header">' . _("Results") . ':</div><br />';
    echo '<table cellpadding="4" border="0"><tr><td class="text"><pre>';

    $cmds = explode("\n", $command);
    foreach ($cmds as $cmd) {
        $cmd = trim($cmd);
        if (strlen($cmd)) {
            unset($results);
            flush();
            echo htmlspecialchars(shell_exec($cmd));
        }
    }

    echo '</pre></td></tr></table><br />';
}
?>

<form action="<?php echo $_SERVER['PHP_SELF'] ?>" method="post">
<?php Util::pformInput() ?>
<textarea class="fixed" name="cmd" rows="10" cols="60">
<?php if (!empty($command)) echo htmlspecialchars($command) ?></textarea>
<br />
<input type="submit" class="button" value="<?php echo _("Execute") ?>">
<?php if ($conf['user']['online_help'] && $browser->hasFeature('javascript')): ?>
    <?php Help::javascript(); ?>
    <td class="header" align="right"><?php echo Help::link('admin', 'admin-cmdshell') ?></td>
<?php endif; ?>

</form>
<?php

require HORDE_TEMPLATES . '/common-footer.inc';

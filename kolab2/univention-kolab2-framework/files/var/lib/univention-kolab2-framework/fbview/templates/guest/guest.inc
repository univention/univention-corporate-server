<?php if ($conf['menu']['always']): ?>
  <table cellpadding="2" cellspacing="0" width="100%">
    <tr><td class="menu">&nbsp;</td></tr>
  </table>
  <br />
<?php endif; ?>

<table border="0" width="300" align="center" cellspacing="0" cellpadding="2">
<tr>
  <td align="center" colspan="4" class="header">
    <b><?php echo _("Guest Services") ?></b>
  </td>
</tr>

<tr>
<?php
$i = 0;
foreach ($guestapps as $app) {
    if ($i % 4 == 0 && $i != 0) {
        echo '</tr><tr>';
    }
    echo Menu::createItem(Horde::url($registry->getInitialPage($app)),
                    $registry->getParam('name', $app), $registry->getParam('icon', $app), '');
    $i++;
}
?>
<tr><td>&nbsp;</td></tr>

<tr><td colspan="4" class="menu"><table border="0"><tr><?php echo Menu::createItem(Horde::url($registry->getInitialPage('horde')),
                          _("Log in"), 'login.gif') ?></tr></table></td>
</tr>
</table>

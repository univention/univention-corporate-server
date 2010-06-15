<table border="0" width="100%" cellpadding="0" cellspacing="0">
<tr>
  <td class="menu"><table border="0" width="100%">
  <tr valign="middle">
    <td class="menuheader" align="left" nowrap="nowrap" width="100%">
      &nbsp;<b><?php echo sprintf(_("Welcome, %s"), $fullname) ?></b>
    </td>
<?php
echo Menu::createItem(Horde::applicationUrl('services/portal/'), _("Home"), 'horde.gif');
if (!$prefs->isLocked('portal_layout')) {
    echo Menu::createItem(Horde::applicationUrl('services/portal/edit.php'), _("Layout"), 'prefs.gif');
}
if (Auth::isAdmin()) {
    echo Menu::createItem(Horde::applicationUrl('admin/'), _("Administration"), 'administration.gif');
}
if (($conf['prefs']['driver'] != '') && ($conf['prefs']['driver'] != 'none')) {
    echo Menu::createItem(Horde::applicationUrl('services/prefs.php?app=horde'), _("Options"), 'prefs.gif');
}

/* Online Help. */
if ($help_link = Help::listLink('horde')) {
    echo Menu::createItem($help_link, _("Help"), 'manual.gif');
}

echo Menu::createItem(Auth::addLogoutParameters(Horde::applicationUrl('login.php'), AUTH_REASON_LOGOUT), _("Log out"), 'logout.gif', null, '_parent', null, '__noselection');
?>
  </tr>
  </table></td>
</tr></table><br />

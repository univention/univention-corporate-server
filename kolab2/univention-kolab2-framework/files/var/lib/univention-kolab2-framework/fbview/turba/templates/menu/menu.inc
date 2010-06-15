<table border="0" cellpadding="0" cellspacing="0" width="100%">
<tr><td class="menu"><table border="0" width="100%"><tr>
<?php

/* Turba menu items */
echo Menu::createItem(Horde::applicationUrl('browse.php'), _("_Browse"), 'user.gif');
echo Menu::createItem(Horde::applicationUrl('add.php'), _("_Add"), 'add.gif');
echo Menu::createItem(Horde::applicationUrl('search.php'), _("_Search"), 'search.gif');

/* Import/Export */
if ($conf['menu']['import_export']) {
    echo Menu::createItem(Horde::applicationUrl('data.php'), _("_Import/Export"), 'data.gif', $registry->getParam('graphics', 'horde'));
}

/* Settings */
if (($conf['prefs']['driver'] != '') && ($conf['prefs']['driver'] != 'none')) {
    echo Menu::createItem(Horde::url($registry->getParam('webroot', 'horde') . '/services/prefs.php?app=turba'), _("_Options"), 'prefs.gif', $registry->getParam('graphics', 'horde'));
}

/* Additional site-specific menu items */
Menu::siteLinks();

/* Online Help */
if ($help_link = Help::listLink('turba')) {
    echo Menu::createItem($help_link, _("_Help"), 'manual.gif', $registry->getParam('graphics', 'horde'));
}

/* Links to other Horde applications. */
Menu::appLinks();
?>
<td width="100%">&nbsp;</td><!-- spacer -->
</tr></table></td></tr></table><br />

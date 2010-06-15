<table border="0" cellpadding="0" cellspacing="0" width="100%">
<tr><td class="menu"><table border="0" width="100%"><tr>
<?php

/* Additional site-specific menu items */
Menu::siteLinks();

/* Online Help */
if ($help_link = Help::listLink('turba')) {
    echo Menu::createItem($help_link, _("Help"), 'manual.gif', $registry->getParam('graphics', 'horde'));
}

/* Links to other Horde applications. */
Menu::appLinks();
?>
<td width="100%">&nbsp;</td><!-- spacer -->
</tr></table></td></tr></table><br />

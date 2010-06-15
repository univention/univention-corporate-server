<?php
$url = Horde::url($registry->getParam('webroot', 'horde') . '/services/help/');
$url = Util::addParameter($url, 'module', $module);
$show_topics = Util::addParameter($url, 'show', 'topics');
$show_about = Util::addParameter($url, 'show', 'about');
?>
<table width="100%" cellspacing="0" cellpadding="4" border="0">
<tr>
  <td class="header" align="left">
    <?php echo Horde::link($show_topics, _("List Help Topics"), 'menuitem', 'help_main') ?><?php echo _("List Help Topics") ?></a>
  </td>
  <td class="header" align="right">
    <?php echo Horde::link($show_about, _("About..."), 'menuitem', 'help_main') ?><?php echo _("About...") ?></a>
  </td>
</tr>
</table>

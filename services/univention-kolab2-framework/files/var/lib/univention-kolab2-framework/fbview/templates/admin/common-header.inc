<table border="0" width="100%" cellpadding="2" cellspacing="0">
<tr>
  <td class="menu"><table border="0" width="100%">
  <tr valign="middle">
<?php
echo Menu::createItem(Horde::applicationUrl('services/portal/'), _("Home"), 'horde.gif');
foreach ($registry->listApps() as $app) {
    if ($registry->hasMethod('admin_list', $app)) {
        $list = $registry->callByPackage($app, 'admin_list');
        if (is_a($list, 'PEAR_Error')) {
            continue;
        }

        foreach ($list as $vals) {
            if ($app != 'horde') {
                $name = $registry->getParam('name', $app);
                if (!empty($vals['name'])) {
                    $name .= ' ' . $vals['name'];
                }
            } else {
                $name = $vals['name'];
            }
            $img = isset($vals['icon']) ? $registry->getParam('graphics', $app) . '/' . $vals['icon'] : $registry->getParam('icon', $app);
            echo Menu::createItem(Horde::url($registry->applicationWebPath($vals['link'], $app)), $name, $img, '');
        }
    }
}
?>
   <td width="100%">&nbsp;</td>
  </tr>
  </table></td>
</tr>
</table>
<br />

<table width="100%" border="0" cellpadding="2" cellspacing="0">
 <tr>
  <td class="header"><?php echo isset($title) ? $title : _("Horde Administration") ?></td>
 </tr>
</table>
<br />
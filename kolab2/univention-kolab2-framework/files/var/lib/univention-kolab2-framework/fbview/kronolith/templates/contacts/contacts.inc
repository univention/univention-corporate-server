<?php echo Help::javascript(); ?>
<form method="post" name="contacts" onsubmit="passAddresses();" action="contacts.php?nocache=<?php echo md5(mt_rand()) ?>">
<?php Util::pformInput() ?>
<table border="0" align="center" cellpadding="0" cellspacing="1">
<tr height="25">
  <td class="header">
    <b><?php echo _("Contact List") ?></b>
  </td>
</tr>

<tr>
  <td>
<table border="0" width="100%" cellpadding="0">
<tr>
  <td class="light" align="left" nowrap="nowrap"><b><?php echo _("Find") ?></b>
    <input value="<?php echo $search ?>" name="search" tabindex="<?php echo $tabindex++ ?>" style="width:150px"></td>
<?php if (count($source_list) > 1): ?>
    <td class="light" align="left" nowrap="nowrap"><b><?php echo _("from") ?></b>
    <select name="source" tabindex="<?php echo $tabindex++ ?>">
    <?php foreach ($source_list as $key => $select): ?>
    <option value="<?php echo $key ?>"<?php if ($key == $source) echo ' selected="selected"' ?>><?php echo htmlspecialchars($select) ?></option>
    <?php endforeach; ?>
    </select></td>
<?php else: ?>
    <td class="light"><input name="source" type="hidden" value="<?php echo key($source_list) ?>" /></td>
<?php endif; ?>
    <td class="light" align="left" nowrap="nowrap"><input type="submit" class="button" value="<?php echo _("Search") ?>" />
  </td>
</tr>
</table>

<tr>
  <td>
<table border="0" width="100%" cellpadding="0">
<tr>
  <td width="45%"><select name="search_results" multiple="multiple" size="10" width="200" onchange="document.contacts.search_results[0].selected=false" ondblclick="addAddress()">
    <option value=""><?php echo _("* Please select address(es) *") ?></option>
    <?php foreach ($addresses as $addr): ?>
      <?php if ($display == 'email'): ?>
        <option value="<?php echo rawurlencode($addr['name']) ?>"><?php echo $addr['email'] ?></option>
      <?php else: ?>
        <option value="<?php echo rawurlencode($addr['email']) ?>"><?php echo $addr['name'] ?></option>
      <?php endif; ?>
    <?php endforeach; ?>
    </select>
  </td>
  <td width="10%" valign="top">
    <input type="button" class="button" style="width:60px" onclick="addAddress();" value="<?php echo _("Add") . " &gt;&gt;" ?>" /><br />&nbsp;<br />
  <td width="45%" colspan="2">
    <select name="selected_addresses" multiple="multiple" size="10" width="200" onchange="document.contacts.selected_addresses[0].selected=false">
      <option value=""><?php echo _("* Add these by clicking Add *") ?></option>
    <?php foreach ($selected_addresses as $value => $text): ?>
      <option value="<?php echo $value ?>"><?php echo $text ?></option>
    <?php endforeach; ?>
    </select>
  </td>
</tr>
<tr>
  <td nowrap="nowrap" align="left" class="light">
    <b><?php echo _("Display") ?></b>
    <select name="display" onchange="changeDisplay();">
      <option value="name"<?php echo $display == "name" ? " selected=\"selected\"" : "" ?>><?php echo _("Name") ?></option>
      <option value="email"<?php echo $display == "email" ? " selected=\"selected\"" : "" ?>><?php echo _("Email Address") ?></option>
    </select>
  </td>
  <td>&nbsp;</td>
  <td colspan="2">
    <input type="button" class="button" onclick="removeAddress()" value="<?php echo _("Delete") ?>" />
    <input type="button" class="button" onclick="saClear();" value="<?php echo _("Reset") ?>" />
  </td>
</tr>
</table>
  </td>
</tr>

<!-- Buttons Row -->
<tr>
  <td class="header" align="right">
    <input type="button" class="button" onclick="updateMessage();" value="<?php echo _("Add") ?>" />
    <input type="button" class="button" onclick="window.close();" value="<?php echo _("Cancel") ?>" />
<?php if ($conf['user']['online_help'] && $browser->hasFeature('javascript')): ?>
    <input type="button" class="button" onclick="<?php echo Help::listLink('kronolith', 'invite-addressbook'); ?>" value="<?php echo _("Help") ?>" />
<?php endif; ?>
  </td>
</tr>
<!-- End Buttons Row -->

</table>

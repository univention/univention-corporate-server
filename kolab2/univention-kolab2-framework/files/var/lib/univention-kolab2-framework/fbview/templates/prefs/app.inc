<table cellpadding="0" cellspacing="0" border="0" width="100%">
<tr>
 <td class="header">
  <?php printf(_("Options for %s"), $registry->getParam('name')) ?>
 </td>
 <td class="header" align="right" nowrap="nowrap">
  <form method="get" name="appswitch">
   <?php echo Util::formInput() ?>
   <span class="smallheader"><?php echo _("Edit options for:") ?></span>
   <select name="app" onchange="document.appswitch.submit();">
     <option value=""></option>
    <?php foreach ($apps as $key => $val): ?>
     <option value="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($val) ?></option>
    <?php endforeach; ?>
   </select>
   <input class="button" type="submit" onclick="if (document.appswitch.app.selectedIndex == 0) return false;" value="<?php echo _("Go") ?>" />
  </form>
 </td>
</tr>
</table>
<br />

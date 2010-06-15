<form method="post" name="export" action="<?php echo Horde::downloadUrl(_("contacts.csv"), null, Horde::applicationUrl('data.php')) ?>">
<input type="hidden" name="actionID" value="export" />
<table cellspacing="0" cellpadding="0" border="0" width="100%">
<tr>
  <td>
    <table cellpadding="3" cellspacing="0" border="0" width="100%">
    <tr><td class="header" align="center"><?php echo _("Export Address Book") ?></td>
    </tr></table>
  </td>
</tr>
<tr>
  <td class="item">
  <table border="0"><tr><td>
    <?php echo _("Select the format to export to:") ?><br />
    <select name="exportID">
      <option value="<?php echo EXPORT_CSV ?>"><?php echo _("Comma separated values") ?></option>
      <option value="<?php echo EXPORT_TSV ?>"><?php echo _("Tab separated values") ?></option>
      <!-- not (yet) implemented -->
      <!--<option value="<?php echo EXPORT_VCARD ?>"><?php echo _("vCard") ?></option>-->
    </select><br /><br />
    <?php echo _("Select the source to export from:") ?><br />
    <select name="source">
      <?php echo $source_options ?>
    </select><br /><br />
    <input type="submit" value="<?php echo _("Export") ?>" class="button" />
  </td></tr></table>
  </td>
</tr>
</table>
</form>

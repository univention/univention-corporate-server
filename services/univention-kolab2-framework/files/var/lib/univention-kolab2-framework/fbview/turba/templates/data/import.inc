<form method="post" name="import_form" enctype="multipart/form-data" action="data.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="<?php echo $next_step ?>" />
<input type="hidden" name="import_step" value="<?php echo $import_step ?>" />
<table cellspacing="0" cellpadding="0" border="0" width="100%">
<tr>
  <td>
    <table cellpadding="3" cellspacing="0" border="0" width="100%">
    <tr><td class="header" align="center"><?php echo sprintf(_("Import Address Book, Step %d"), $import_step) ?></td>
    </tr></table>
  </td>
</tr>
<tr>
  <td class="item">
  <table border="0"><tr><td>
    <?php echo _("Select the format to import from:") ?><br />
    <select name="import_format">
      <option value="csv"><?php echo _("Comma separated values") ?></option>
      <option value="tsv"><?php echo _("Tab separated values") ?></option>
      <option value="vcard"><?php echo _("vCard") ?></option>
      <option value="mulberry"><?php echo _("Mulberry Address Book") ?></option>
      <option value="pine"><?php echo _("Pine Address Book") ?></option>
    </select><br /><br />
    <?php echo _("Select the destination to import to:") ?><br />
    <select name="dest">
      <?php echo $dest_options ?>
    </select><br /><br />
    <?php echo _("Select the file to import:") ?><br />
    <input type="file" name="import_file" class="fixed" size="40" /><br /><br />
    <input type="submit" value="<?php echo _("Next") ?>" class="button" />
  </td></tr></table>
  </td>
</tr>
</table>
</form>

<br />

<form name="directory_list" action="<?php echo Horde::applicationUrl('browse.php') ?>" method="get">
<?php echo Util::formInput() ?>
<table border="0" align="center" width="100%" cellpadding="0" cellspacing="0">
<tr>
  <td>
    <table border="0" width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td class="header">
        <b><?php echo _("Select Address Book") ?>&nbsp;&nbsp;</b>
        <select name="source" onchange="document.directory_list.submit();"><?php echo $source_options ?></select>
        <input class="button" type="submit" value="<?php echo _("Show") ?>" />
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>
</form>
<br />

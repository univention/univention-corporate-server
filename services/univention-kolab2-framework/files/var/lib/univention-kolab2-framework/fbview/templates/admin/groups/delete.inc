<form name="delete" method="post" action="groups.php">
<input type="hidden" name="actionID" value="deleteform" />
<input type="hidden" name="cid" value="<?php echo $group->getId() ?>" />
<?php Util::pformInput() ?>

<table border="0" width="100%" cellpadding="1" cellspacing="1">
<tr>
  <td class="header" align="left" width="100%" colspan="7">
    <span class="smallheader"><?php echo Horde::img('group.gif') ?>&nbsp;<b><?php echo sprintf(_("Are you sure you wish to delete '%s' and any sub-groups?"), $group->getShortName()) ?></b></span>
  </td>
</tr>
<tr>
  <td><input type="submit" class="button" name="confirm" value="<?php echo _("Delete") ?>" />
      <input type="submit" class="button" name="confirm" value="<?php echo _("Cancel") ?>" /></td>
</tr>

</table>
</form>
<br />

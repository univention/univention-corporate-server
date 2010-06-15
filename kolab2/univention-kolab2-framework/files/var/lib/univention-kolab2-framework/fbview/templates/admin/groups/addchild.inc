<form name="add_child" method="post" action="groups.php">
<input type="hidden" name="actionID" value="addchildform" />
<input type="hidden" name="cid" value="<?php echo (int)Util::getFormData('cid') ?>" />
<?php Util::pformInput() ?>

<table border="0" width="100%" cellpadding="1" cellspacing="1">
<tr>
  <td class="header" align="left" width="100%"><span class="smallheader">
    <?php echo Horde::img('group.gif') ?>&nbsp;<b><?php echo sprintf(_("Add a child group to '%s'"), $gname) ?></b>
  </span></td>
</tr>
<tr>
  <td><input type="text" name="child" /></td>
</tr>
<tr>
  <td><input type="submit" class="button" value="<?php echo _("Add") ?>" /></td>
</tr>

</table>
</form>
<br />

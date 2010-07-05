<form name="delete" method="post" action="groups.php">
<input type="hidden" name="actionID" value="deleteform" />
<input type="hidden" name="cid" value="<?php echo htmlspecialchars($group->getId()) ?>" />
<?php Util::pformInput() ?>

<h1 class="header">
 <?php echo Horde::img('group.png') ?>&nbsp;<?php printf(_("Are you sure you wish to delete \"%s\" and any sub-groups?"), htmlspecialchars($group->getShortName())) ?>
</h1>

<input type="submit" class="button" name="confirm" value="<?php echo _("Delete") ?>" />
<input type="submit" class="button" name="confirm" value="<?php echo _("Cancel") ?>" />
</form>
<br />

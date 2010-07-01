<form name="add_child" method="post" action="groups.php">
<input type="hidden" name="actionID" value="addchildform" />
<input type="hidden" name="cid" value="<?php echo $cid ?>" />
<?php Util::pformInput() ?>

<h1 class="header">
 <?php echo Horde::img('group.png') ?>&nbsp;<?php printf(_("Add a child group to \"%s\""), htmlspecialchars($gname)) ?>
</h1>

<label for="child" class="hidden"><?php echo _("Child") ?></label>
<input type="text" id="child" name="child" />
<input type="submit" class="button" value="<?php echo _("Add") ?>" />
</form>
<br />

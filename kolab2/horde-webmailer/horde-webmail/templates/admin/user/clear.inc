<form name="clearuser" method="post">
<input type="hidden" name="form" value="clear" />

<h1 class="header">
 <?php printf(_("Clear out user: %s"), $f_user_name) ?>
</h1>
<p class="item">
 <strong><?php printf(_("Really remove user data for user \"%s\"? This operation cannot be undone."), $f_user_name) ?></strong>
</p>
<p class="control">
 <input type="submit" class="button" name="submit" value="<?php echo _("Clear user") ?>" />
 <input type="submit" class="button" name="submit" value="<?php echo _("Cancel") ?>" />
</p>
</form>

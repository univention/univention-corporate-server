<form name="removeuser" method="post">
<input type="hidden" name="form" value="remove" />

<h1 class="header">
 <?php printf(_("Remove user: %s"), $f_user_name) ?>
</h1>
<p class="item">
 <strong><?php printf(_("Really delete \"%s\"? This operation cannot be undone."), $f_user_name) ?></strong>
</p>
<p class="control">
 <input type="submit" class="button" name="submit" value="<?php echo _("Remove user") ?>" />
 <input type="submit" class="button" name="submit" value="<?php echo _("Cancel") ?>" />
</p>
</form>

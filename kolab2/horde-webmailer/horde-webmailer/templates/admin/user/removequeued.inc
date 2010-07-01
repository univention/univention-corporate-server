<form method="post" action="<?php echo Horde::selfUrl() ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="form" value="removequeued" />
<input type="hidden" name="user_name" value="<?php echo $f_user_name ?>" />

<h1 class="header">
 <?php echo _("Pending Signups:") ?>
</h1>
<p class="item">
 <?php printf(_("Are you sure you want to remove the signup request for \"%s\"?"), $f_user_name) ?>
</p>
<p class="control">
  <input class="button" type="submit" value="<?php echo _("Remove") ?>" />
</p>
</form>

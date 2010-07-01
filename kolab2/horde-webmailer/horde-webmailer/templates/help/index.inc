<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "DTD/xhtml1-frameset.dtd">
<html>
<head>
 <title><?php echo _("Help") ?></title>
</head>

<frameset cols="<?php echo ($rtl ? '*,' : '') . '200' . ($rtl ? '' : ',*') ?>" id="horde_help_frame">
<?php if (!$rtl): ?>
 <frame name="help_sidebar" src="<?php echo $sidebar_url ?>" scrolling="auto" />
<?php endif; ?>
 <frameset rows="30,*">
  <frame name="help_menu" id="help_menu" frameborder="0" scrolling="no" src="<?php echo $menu_url ?>" />
  <frame name="help_main" id="help_main" frameborder="0" src="<?php echo $main_url ?>" />
 </frameset>
<?php if ($rtl): ?>
 <frame name="help_sidebar" src="<?php echo $sidebar_url ?>" scrolling="auto" />
<?php endif; ?>
</frameset>

</html>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "DTD/xhtml1-frameset.dtd">
<html>
<head>
  <link rel="SHORTCUT ICON" href="<?php echo $registry->getParam('graphics')?>/favicon.ico"  />
  <title><?php echo $registry->getParam('name'); ?></title>
</head>

<frameset cols="150,*" border="0" id="hf" framespacing="0" frameborder="0">
  <frame name="horde_menu" src="<?php echo Horde::applicationUrl('services/portal/menu.php') ?>" scrolling="auto" marginheight="0" marginwidth="0" frameborder="0" noresize="noresize" />
  <frame name="horde_main" src="<?php echo $main_page ?>" scrolling="<?php echo $scrollbar ?>" marginheight="0" marginwidth="0" frameborder="0" noresize="noresize" />
</frameset>

</html>

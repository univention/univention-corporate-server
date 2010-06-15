<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "DTD/xhtml1-frameset.dtd">
<html>
<head>
    <link rel="SHORTCUT ICON" href="<?php echo $registry->getParam('graphics', 'horde')?>/favicon.ico" />
    <title><?php echo $registry->getParam('name'); ?></title>
</head>

<frameset rows="*, 20" border="0">
    <frame name="turba_main" src="<?php echo Horde::applicationUrl('browse.php') ?>" scrolling="yes" noresize="noresize" frameborder="0" />
    <frame name="turba_menu" src="<?php echo Horde::applicationUrl('miniwindow.php?menu=1') ?>" scrolling="no" marginheight="2" marginwidth="2" noresize="noresize" frameborder="0" />
</frameset>

</html>

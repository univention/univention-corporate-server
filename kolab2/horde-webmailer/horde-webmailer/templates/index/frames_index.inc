<?php $rtl = isset($nls['rtl'][$language]) ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "DTD/xhtml1-frameset.dtd">
<html>
<head>
 <link rel="SHORTCUT ICON" href="<?php echo $registry->getImageDir() ?>/favicon.ico" />
 <title><?php echo htmlspecialchars($registry->get('name')) ?></title>
</head>

<frameset id="hf" cols="<?php echo ($rtl ? '*,' : '') . (isset($prefs) ? $prefs->getValue('sidebar_width') : 150) . ($rtl ? '' : ',*') ?>" framespacing="0" frameborder="0">
<?php if ($rtl): ?>
  <frame name="horde_main" src="<?php echo Util::addParameter(htmlspecialchars($main_page), 'frameset_loaded', 1) ?>" scrolling="<?php echo $scrollbar ?>" noresize="noresize" />
  <frame name="horde_menu" src="<?php echo Horde::applicationUrl('services/portal/sidebar.php') ?>" scrolling="auto" noresize="noresize" />
<?php else: ?>
  <frame name="horde_menu" src="<?php echo Horde::applicationUrl('services/portal/sidebar.php') ?>" scrolling="auto" noresize="noresize" />
  <frame name="horde_main" src="<?php echo Util::addParameter(htmlspecialchars($main_page), 'frameset_loaded', 1) ?>" scrolling="<?php echo $scrollbar ?>" noresize="noresize" />
<?php endif; ?>
</frameset>

</html>

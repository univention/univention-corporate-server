<?php
if (isset($language)) {
    header('Content-type: text/html; charset=' . NLS::getCharset());
    header('Vary: Accept-Language');
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">
<!--  Nag: Copyright 2001-2009 The Horde Project.  Nag is under the GPL.   -->
<!-- Horde Project: http://www.horde.org/ | Nag: http://www.horde.org/nag/ -->
<!--       GNU Public License: http://www.fsf.org/copyleft/gpl.html        -->
<?php echo !empty($language) ? '<html lang="' . strtr($language, '_', '-') . '">' : '<html>' ?>
<head>
<?php

$page_title = $registry->get('name');
if (!empty($title)) $page_title .= ' :: ' . $title;
if (!empty($refresh_time) && ($refresh_time > 0) && !empty($refresh_url)) {
    echo "<meta http-equiv=\"refresh\" content=\"$refresh_time;url=$refresh_url\">\n";
}

Horde::includeScriptFiles();

$bc = Util::nonInputVar('bodyClass');
if ($prefs->getValue('show_panel')) {
    if ($bc) {
        $bc .= ' ';
    }
    $bc .= 'rightPanel';
}

?>
<title><?php echo htmlspecialchars($page_title) ?></title>
<link href="<?php echo $GLOBALS['registry']->getImageDir()?>/favicon.ico" rel="SHORTCUT ICON" />
<?php echo Horde::stylesheetLink('nag', empty($print_view) ? '' : 'print') ?>
<link href="<?php echo Horde::applicationUrl('themes/categoryCSS.php') ?>" rel="stylesheet" type="text/css" />
</head>

<body<?php if ($bc) echo ' class="' . $bc . '"' ?><?php if ($bi = Util::nonInputVar('bodyId')) echo ' id="' . $bi . '"'; ?>>

<?php
global $language;
if (isset($language)) {
    header('Content-type: text/html; charset=' . NLS::getCharset());
    header('Vary: Accept-Language');
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">
<!--  MIMP: Copyright 2001-2009 The Horde Project.  MIMP is under the GPL.   -->
<!-- Horde Project: http://www.horde.org/ | MIMP: http://www.horde.org/mimp/ -->
<!--       GNU Public License: http://www.fsf.org/copyleft/gpl.html          -->
<?php
echo (!empty($language)) ? '<html lang="' . strtr($language, '_', '-') . '"' : '<html';
echo (!empty($ie_clientcaps)) ? ' xmlns:IE>' : '>';
?>
<head>
<?php

$page_title = $registry->get('name');
if (!empty($title)) $page_title .= ' :: ' . $title;
if (!empty($refresh_time) && !empty($refresh_url)) {
    echo "<meta http-equiv=\"refresh\" content=\"$refresh_time;url=$refresh_url\" />\n";
}
Horde::includeScriptFiles();
?>
<title><?php echo htmlspecialchars($page_title) ?></title>
<?php if (!$GLOBALS['browser']->isMobile()): ?>
<link href="<?php echo $GLOBALS['registry']->getImageDir()?>/favicon.ico" rel="SHORTCUT ICON" />
<?php endif; ?>
<?php echo Horde::stylesheetLink('mimp', empty($printer_friendly) ? '' : 'print') ?>
</head>

<body<?php if ($bc = Util::nonInputVar('bodyClass')) echo ' class="' . $bc . '"' ?><?php if ($bi = Util::nonInputVar('bodyId')) echo ' id="' . $bi . '"'; ?>>

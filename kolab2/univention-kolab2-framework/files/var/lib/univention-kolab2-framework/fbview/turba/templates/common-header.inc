<?php
if (isset($language)) {
    header('Content-type: text/html; charset=' . NLS::getCharset());
    header('Vary: Accept-Language');
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">
<!-- Turba: Copyright 2000-2004, The Horde Project. Turba is under the GPL. -->
<!--   Horde Project: http://horde.org/ | Turba: http://horde.org/turba/    -->
<!--       GNU Public License: http://www.fsf.org/copyleft/gpl.html         -->
<?php echo !empty($language) ? '<html lang="' . strtr($language, '_', '-') . '">' : '<html>' ?>
<head>
<?php

$page_title = $registry->getParam('name');
if (!empty($title)) $page_title .= ' :: ' . $title;
if (!empty($refresh_time) && ($refresh_time > 0) && !empty($refresh_url)) {
    echo "<meta http-equiv=\"refresh\" content=\"$refresh_time;url=$refresh_url\">\n";
}
Horde::includeScriptFiles();
?>
<title><?php echo $page_title ?></title>
<?php echo Horde::stylesheetLink('turba') ?>
</head>

<body<?php if (Util::nonInputVar('bodyClass')) echo ' class="' . $bodyClass . '"' ?>>

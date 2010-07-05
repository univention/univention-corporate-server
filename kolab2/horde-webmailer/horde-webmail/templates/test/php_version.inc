<h1>PHP Version</h1>
<ul>
<?php if (!empty($test_app) && Util::nonInputVar('test_app') == 'horde'): ?>
    <li><a href="<?php echo $php_info->phpinfo ?>">View phpinfo() screen</a></li>
    <li><a href="<?php echo $php_info->extensions ?>">View loaded extensions</a></li>
<?php endif; ?>
    <li>PHP Version: <?php echo $php_info->version ?></li>
    <li>PHP Major Version: <?php echo $php_info->major ?></li>
<?php if (isset($php_info->minor)): ?>
    <li>PHP Minor Version: <?php echo $php_info->minor ?></li>
<?php endif; ?>
<?php if (isset($php_info->subminor)): ?>
    <li>PHP Subminor Version: <?php echo $php_info->subminor ?></li>
<?php endif; ?>
    <li>PHP Version Classification: <?php echo $php_info->class ?></li>
    <li style="color:<?php echo $php_info->status_color ?>"><strong><?php echo $php_info->status ?></strong></li>
<?php if (isset($php_info->version_check)): ?>
    <li><?php echo $php_info->version_check ?></li>
<?php endif; ?>
<?php if (isset($php_info->insecure)): ?>
    <li style="color:orange"><strong><?php echo $php_info->insecure ?><strong></li>
<?php endif; ?>
</ul>

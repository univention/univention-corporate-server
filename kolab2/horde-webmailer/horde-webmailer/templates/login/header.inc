<div id="menu">
<?php
$menu = new Menu(HORDE_MENU_MASK_NONE);
$hmenu = $menu->render();
if ($hmenu): ?>
 <span class="leftFloat"><?php echo $hmenu ?></span>
<?php endif; ?>
 <h1 style="text-align:center"><?php printf(_("Welcome to %s"), $registry->get('name')) ?></h1>
</div>

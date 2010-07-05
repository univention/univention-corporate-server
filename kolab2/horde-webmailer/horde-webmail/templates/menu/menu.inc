<div id="menu">
 <div class="leftFloat">
<?php
if (!(isset($menu) && is_a($menu, 'Menu'))) {
    require_once 'Horde/Menu.php';
    $menu = new Menu();
    $status = $GLOBALS['registry']->get('status', 'horde');
    if (!($status == 'notoolbar' || $status == 'hidden' || $status == 'inactive')) {
        $menu->add(Horde::applicationUrl('services/portal/'), _("_Home"), 'horde.png', $GLOBALS['registry']->getImageDir('horde'));
    }
}
echo $menu->render();
?>
 </div>
</div>

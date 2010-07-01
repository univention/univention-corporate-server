<div id="menu">
 <div class="leftFloat">
<?php
$menu = new Menu(HORDE_MENU_MASK_NONE);
$list = $registry->callByPackage('horde', 'admin_list');
if (!is_a($list, 'PEAR_Error')) {
    foreach ($list as $vals) {
        $img = isset($vals['icon']) ? $registry->getImageDir() . '/' . $vals['icon'] : $registry->get('icon');
        $menu->add(Horde::url($registry->applicationWebPath($vals['link'])), $vals['name'], $img, '');
    }
}
echo $menu->render();
?>
 </div>
</div>
<?php $notification->notify(array('listeners' => 'status'));

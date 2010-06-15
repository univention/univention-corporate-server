<div id="menu">
<?php
require_once 'Horde/Menu.php';

$menu = new Menu(HORDE_MENU_MASK_NONE);
if (in_array(INGO_STORAGE_ACTION_VACATION, $_SESSION['ingo']['script_categories'])) {
	$menu->add(Horde::applicationUrl('../ingo-vacation'), _("_Vacation"), 'vacation.png');
}

$menu->add(Horde::url(Auth::addLogoutParameters($GLOBALS['registry']->get('webroot', 'horde') . '/login.php?url='. Horde::selfUrl(true) , AUTH_REASON_LOGOUT)),
    _("_Log out"), 'logout.png', $registry->getImageDir('horde'));
?>
<img alt="" src="<?php echo $registry->getImageDir('horde')?>/logo_white_grey.png" style="float: left;" />
<?php echo $menu->render () ?>
</div>

<?php $GLOBALS['notification']->notify(array('listeners' => 'status')) ?>

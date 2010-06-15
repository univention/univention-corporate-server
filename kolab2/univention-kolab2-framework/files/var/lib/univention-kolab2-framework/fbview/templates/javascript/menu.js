function correctWidthForScrollbar()
{
<?php if ($GLOBALS['browser']->hasQuirk('scrollbar_in_way')): ?>
    // Correct for frame scrollbar in IE by determining if a scrollbar is present,
    // and if not readjusting the marginRight property to 0
    // See http://www.xs4all.nl/~ppk/js/doctypes.html for why this works
    if (document.documentElement.clientHeight == document.documentElement.offsetHeight) {
        // no scrollbar present, take away extra margin
        document.body.style.marginRight = '0px';
    } else {
        document.body.style.marginRight = '15px';
    }
<?php endif; ?>
}

<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
var shown = new Array();

document.write('<style type="text/css">');
document.write('.para {display: none}');
document.write('</style>');

function toggle(i)
{
    shown[i] = shown[i] ? shown[i] : false;
    shown[i] = !shown[i];
    var current = shown[i] ? 'block' : 'none';
    var state = shown[i] ? 'expanded' : 'collapsed';

    if (document.getElementById && document.getElementById('menu_' + i)) {
        document.getElementById('menu_' + i).style.display = current;
        document.getElementById('arrow_' + i).src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') . '/tree/arrow-' ?>' + state + '.gif';
    } else if (document.all && document.all['menu_' + i]) {
        document.all['menu_' + i].style.display = current;
        document.all['arrow_' + i].src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') . '/tree/arrow-' ?>' + state + '.gif';
    }

    correctWidthForScrollbar();
}
<?php else: ?>
function toggle(i)
{
    return false;
}
<?php endif; ?>

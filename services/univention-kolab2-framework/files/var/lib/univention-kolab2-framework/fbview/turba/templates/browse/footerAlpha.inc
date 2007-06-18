</tr>
</table>
<table border="0" cellspacing="0" cellpadding="1" width="100%">
<tr>
  <td class="control" width="100%" align="center">
<?php
$show = Util::getFormData('show', 'all');
$currentPage = String::upper($page);
if ($currentPage == '*') {
    echo '<b>(' . _("All") . ')</b>&nbsp;';
} else {
    echo Horde::link(Horde::applicationUrl(Util::addParameter($viewurl, array('page' => '*',
                                                                              'show' => $show)))) . _("All") . '</a>&nbsp;';
}
for ($i = 65; $i < 91; $i++) {
    $a = chr($i);
    if ($currentPage == $a) {
        echo '<b>(' . $a . ')</b>&nbsp;';
    } else {
        $link = Util::addParameter($viewurl, array('page' => $a,
                                                   'show' => $show));
        echo Horde::link(Horde::applicationUrl($link)) . $a . '</a>&nbsp;';
    }
}
?>
  </td>
</tr>
</table>

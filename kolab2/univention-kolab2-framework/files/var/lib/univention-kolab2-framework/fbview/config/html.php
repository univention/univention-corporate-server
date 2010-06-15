<?php
/**
 * Base Horde CSS properties.
 * This file is parsed by css.php, and used to produce a stylesheet.
 *
 * $Horde: horde/config/html.php.dist,v 1.91 2004/05/23 18:19:04 jan Exp $
 */

$css['body']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['body']['font-size'] = '12px';
$css['body']['background-color'] = '#222244';
$css['body']['color'] = 'black';
if ($browser->hasQuirk('scrollbar_in_way')) {
    $css['body']['margin-right'] = '15px';
}
$css['body']['scrollbar-base-color'] = '#666699';
$css['body']['scrollbar-arrow-color'] = '#ddddff';
$css['html']['scrollbar-base-color'] = '#666699';
$css['html']['scrollbar-arrow-color'] = '#ddddff';

$css['img']['border'] = 'none';

$css['.box']['border'] = '1px dashed #999999';
$css['.box']['background-color'] = 'white';

$css['.solidbox']['border'] = '1px solid black';

$css['.greybox']['border'] = '1px solid black';
$css['.greybox']['background-color'] = '#e9e9e9';

$css['.whitebox']['border'] = '1px solid black';
$css['.whitebox']['background-color'] = 'white';

$css['.headerbox']['border-left'] = '1px solid #666699';
$css['.headerbox']['border-right'] = '1px solid #666699';
$css['.headerbox']['border-bottom'] = '1px solid #666699';

$css['.nomargin']['padding'] = '0px';
$css['.nomargin']['margin'] = '0px 0px';

$css['input']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['input']['font-size'] = '12px';

$css['select']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['select']['font-size'] = '12px';
$css['select']['font-weight'] = 'normal';

$css['form']['margin'] = '0px';

$css['.form-error']['color'] = '#ff0000';
$css['.form-header']['font-weight'] = 'bold';

$css['a']['color'] = '#333399';
$css['a']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['a']['font-size'] = '12px';
$css['a']['text-decoration'] = 'none';
$css['a:hover']['color'] = 'blue';
$css['a:hover']['text-decoration'] = 'underline';

$css['a.menuitem']['color'] = '#eeeeff';
$css['a.menuitem']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['a.menuitem']['font-size'] = '11px';
$css['a.menuitem']['font-weight'] = 'normal';
$css['a.menuitem:hover']['color'] = 'yellow';

$css['a.helpitem']['color'] = '#cccccc';
$css['a.helpitem']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['a.helpitem']['font-size'] = '12px';
$css['a.helpitem']['font-weight'] = 'normal';
$css['a.helpitem:hover']['color'] = 'yellow';

$css['a.helplink']['color'] = 'white';
$css['a.helplink']['background-color'] = '#444466';
$css['a.helplink']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['a.helplink']['text-decoration'] = 'underline';
$css['a.helplink:hover']['color'] = 'yellow';

$css['.selected']['background-color'] = '#bbcbff';
$css['.selected-hi']['background-color'] = '#cceeff';

$css['.widget']['color'] = '#222244';
$css['.widget']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['.widget']['font-size'] = '11px';
$css['a.widget:hover']['color'] = 'blue';
$css['a.widget:hover']['background-color'] = &$css['.selected']['background-color'];

$css['.notice']['background-color'] = '#ffffcc';

$css['.outline']['background-color'] = 'black';

$css['.menu']['color'] = 'white';
$css['.menu']['background-color'] = '#444466';
$css['.menu']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['.menu']['height'] = '55px';

$css['.menuselected']['background-color'] = '#666688';
$css['.menuselected']['border-bottom'] = '1px solid #9999cc';
$css['.menuselected']['border-right'] = '1px solid #9999cc';
$css['.menuselected']['border-top'] = '1px solid #222244';
$css['.menuselected']['border-left'] = '1px solid #222244';
$css['.menuselected']['padding'] = '2px';

$css['.menuheader']['color'] = '#ccccee';
$css['.menuheader']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['.menuheader']['font-weight'] = 'bold';
$css['.menuheader']['font-size'] = '17px';

$css['.header']['color'] = '#ccccee';
$css['.header']['background-color'] = '#444466';
$css['.header']['height'] = '25px';
$css['.header']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['.header']['font-weight'] = 'bold';
$css['.header']['font-size'] = '15px';
$css['td.header']['padding-left'] = '3px';
$css['td.header']['padding-right'] = '3px';
$css['a.header:hover']['color'] = 'white';

$css['.light']['color'] = 'white';
$css['.light']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['.light']['font-size'] = '12px';

$css['.smallheader']['color'] = '#ccccee';
$css['.smallheader']['background-color'] = '#444466';
$css['.smallheader']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['.smallheader']['font-size'] = '12px';
$css['.smallheader a:hover']['color'] = 'white';
$css['a.smallheader:hover']['color'] = 'white';

$css['.small']['color'] = '#aaaacc';
$css['.small']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['.small']['font-size'] = '11px';

$css['.legend']['color'] = '#000000';
$css['.legend']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';
$css['.legend']['font-size'] = '11px';

$css['.control']['color'] = 'black';
$css['.control']['background-color'] = '#cccccc';
$css['.control']['border-bottom'] = '1px solid #999999';

$css['.item']['color'] = 'black';
$css['.item']['background-color'] = '#eeeeee';

$css['.accessKey']['text-decoration'] = 'underline';

$css['.button']['color'] = 'white';
$css['.button']['background-color'] = '#666699';
$css['.button']['border-bottom'] = '1px solid #222244';
$css['.button']['border-right'] = '1px solid #222244';
$css['.button']['border-top'] = '1px solid #9999cc';
$css['.button']['border-left'] = '1px solid #9999cc';
$css['.button']['font-size'] = '11px';
$css['.button']['font-family'] = 'Verdana,Helvetica,sans-serif';
$css['.button']['font-weight'] = 'normal';

$css['.text']['color'] = 'black';
$css['.text']['background-color'] = 'white';
$css['.text-hi']['background-color'] = '#f3f3f3';

$css['.summarytext'] = $css['.text'];
$css['td.summarytext']['padding'] = '3px';

$css['.summary']['background-color'] = 'white';

$css['.item0']['background-color'] = '#eeeeee';
$css['.item1']['background-color'] = '#dddddd';

$css['.fixed']['font-size'] = '13px';
$css['.fixed']['font-family'] = 'monospace, fixed';

$css['td']['font-size'] = '12px';
$css['td']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';

$css['th']['font-size'] = '12px';
$css['th']['font-family'] = 'Geneva,Arial,Helvetica,sans-serif';

$css['.signature']['color'] = '#cccccc';
$css['.signature-fixed']['color'] = '#cccccc';
$css['.signature-fixed']['font-size'] = '13px';
$css['.signature-fixed']['font-family'] = 'monospace, fixed';

$css['.quoted1']['color'] = '#660066';
$css['.quoted2']['color'] = '#007777';
$css['.quoted3']['color'] = '#990000';
$css['.quoted4']['color'] = '#000099';
$css['.quoted5']['color'] = '#bb6600';

$css['.tooltip']['font-size'] = '11px';
$css['.tooltip']['background-color'] = '#ffffcc';
$css['.tooltip']['border'] = '1px solid black';

$css['.sidebar'] = array();
$css['.sidebar-panel'] = array();
$css['a.sidebaritem'] = array();

$css['.tabset']['border-bottom-width'] = '1px';
$css['.tabset']['border-bottom-style'] = 'solid';
$css['.tabset']['border-bottom-color'] = &$css['.header']['background-color'];

$css['.tab']['color'] = &$css['.item']['color'];
$css['.tab']['background-color'] = &$css['.item']['background-color'];
$css['.tab']['-moz-border-radius-topleft'] = '10px';
$css['.tab']['-moz-border-radius-topright'] = '10px';
$css['.tab']['cursor'] = 'pointer';

$css['.tab-hi']['color'] = &$css['.header']['color'];
$css['.tab-hi']['background-color'] = &$css['.header']['background-color'];
$css['.tab-hi']['-moz-border-radius-topleft'] = '10px';
$css['.tab-hi']['-moz-border-radius-topright'] = '10px';
$css['.tab-hi']['cursor'] = 'pointer';
$css['a.tab-hi:hover']['color'] = 'white';

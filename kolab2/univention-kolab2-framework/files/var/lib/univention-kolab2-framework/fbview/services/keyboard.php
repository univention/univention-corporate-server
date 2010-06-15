<?php
/*
 * $Horde: horde/services/keyboard.php,v 1.12 2004/01/01 15:17:00 jan Exp $
 *
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';

$title = _("Special Character Input");
require HORDE_TEMPLATES . '/common-header.inc';

?>

<script language="Javascript" type="text/javascript">

var target;

function handleListChange(theList) {
    var numSelected = theList.selectedIndex;
    
    if (numSelected != 0) {
        document.characters.textbox.value += theList.options[numSelected].value;
        theList.selectedIndex = 0;
    }
}
</script>

<form name="characters">
<table border="0" cellspacing="0" cellpadding="2">
  <tr>
    <td align="left">
      <p class="smallheader"><?php echo _("Select the characters you need from the boxes below. You can then copy and paste them from the text area.") ?></p>
    </td>
  </tr>
  <tr>
    <td align="left">
      <table border="0" cellspacing="0" cellpadding="0">
        <tr>
          <td align="center">
            <select name="a" onchange="handleListChange(this)">
              <option value="a" selected> a </option>
              <option value="&#192;"> &#192; </option>
              <option value="&#224;"> &#224; </option>
              <option value="&#193;"> &#193; </option>
              <option value="&#225;"> &#225; </option>
              <option value="&#194;"> &#194; </option>
              <option value="&#226;"> &#226; </option>
              <option value="&#195;"> &#195; </option>
              <option value="&#227;"> &#227; </option>
              <option value="&#196;"> &#196; </option>
              <option value="&#228;"> &#228; </option>
              <option value="&#197;"> &#197; </option>
              <option value="&#229;"> &#229; </option>
            </select>
          </td>
          <td align="center"> 
            <select name="e" onchange="handleListChange(this)">
              <option value="e" selected> e </option>
              <option value="&#200;"> &#200; </option>
              <option value="&#232;"> &#232; </option>
              <option value="&#201;"> &#201; </option>
              <option value="&#233;"> &#233; </option>
              <option value="&#202;"> &#202; </option>
              <option value="&#234;"> &#234; </option>
              <option value="&#203;"> &#203; </option>
              <option value="&#235;"> &#235; </option>
            </select>
          </td>
          <td align="center"> 
            <select name="i" onchange="handleListChange(this)">
              <option value="i" selected> i </option>
              <option value="&#204;"> &#204; </option>
              <option value="&#236;"> &#236; </option>
              <option value="&#205;"> &#205; </option>
              <option value="&#237;"> &#237; </option>
              <option value="&#206;"> &#206; </option>
              <option value="&#238;"> &#238; </option>
              <option value="&#207;"> &#207; </option>
              <option value="&#239;"> &#207; </option>
            </select>
          </td>
          <td align="center"> 
            <select name="o" onchange="handleListChange(this)">
              <option value="o" selected> o </option>
              <option value="&#210;"> &#210; </option>
              <option value="&#242;"> &#242; </option>
              <option value="&#211;"> &#211; </option>
              <option value="&#243;"> &#243; </option>
              <option value="&#212;"> &#212; </option>
              <option value="&#244;"> &#244; </option>
              <option value="&#213;"> &#213; </option>
              <option value="&#245;"> &#245; </option>
              <option value="&#214;"> &#214; </option>
              <option value="&#246;"> &#246; </option>
            </select>
          </td>
          <td align="center"> 
            <select name="u" onchange="handleListChange(this)">
              <option value="u" selected> u </option>
              <option value="&#217;"> &#217; </option>
              <option value="&#249;"> &#249; </option>
              <option value="&#218;"> &#218; </option>
              <option value="&#250;"> &#250; </option>
              <option value="&#219;"> &#219; </option>
              <option value="&#251;"> &#251; </option>
              <option value="&#220;"> &#220; </option>
              <option value="&#252;"> &#252; </option>
            </select>
          </td>
          <td align="center"> 
            <select name="Other" onchange="handleListChange(this)">
              <option value="misc" selected> <?php echo _("Other"); ?></option>
              <option value="&#162;"> &#162; </option>
              <option value="&#163;"> &#163; </option>
              <option value="&#164;"> &#164; </option>
              <option value="&#165;"> &#165; </option>
              <option value="&#198;"> &#198; </option>
              <option value="&#230;"> &#230; </option>
              <option value="&#223;"> &#223; </option>
              <option value="&#199;"> &#199; </option>
              <option value="&#231;"> &#231; </option>
              <option value="&#209;"> &#209; </option>
              <option value="&#241;"> &#241; </option>
              <option value="&#253;"> &#253; </option>
              <option value="&#255;"> &#255; </option>
              <option value="&#191;"> &#191; </option>
              <option value="&#161;"> &#161; </option>
            </select>
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td align="left" class="fixed">
      <textarea rows="4" cols="25" class="fixed" name="textbox"></textarea>
    </td>
  </tr>
  <tr>
    <td align="center">
      <input type="button" class="button" onclick="window.close();" name="close" value="<?php echo _("Close Window") ?>" />
    </td>
  </tr>
</table>
</form>
</body>
</html>

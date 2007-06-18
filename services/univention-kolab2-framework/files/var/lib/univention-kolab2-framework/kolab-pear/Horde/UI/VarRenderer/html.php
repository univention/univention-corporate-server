<?php
/**
 * The Horde_UI_VarRenderer_html:: class renders variables to HTML.
 *
 * $Horde: framework/UI/UI/VarRenderer/html.php,v 1.43 2004/05/26 03:10:46 chuck Exp $
 *
 * Copyright 2003-2004 Jason M. Felice <jfelice@cronosys.com>
 *
 * See the enclosed file LICENSE for license information (LGPL).
 *
 * @version $Revision: 1.1.2.1 $
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_VarRenderer_html extends Horde_UI_VarRenderer {

    var $_onLoadJS = array();

    function _renderVarInputDefault(&$form, &$var, &$vars)
    {
        return '<strong>Warning:</strong> Unknown variable type ' .
            $var->getTypeName();
    }

    function _renderVarInput_number(&$form, &$var, &$vars)
    {
        $value = $var->getValue($vars);
        $linfo = NLS::getLocaleInfo();
        /* Only if there is a mon_decimal_point do the
         * substitution. */
        if (!empty($linfo['mon_decimal_point'])) {
            $value = str_replace('.', $linfo['mon_decimal_point'], $value);
        }
        return sprintf('<input type="text" size="5" name="%s" value="%s"%s />',
                       $var->getVarName(),
                       $value,
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_int(&$form, &$var, &$vars)
    {
        return sprintf('<input type="text" size="5" name="%s" value="%s"%s />',
                       $var->getVarName(),
                       $value = $var->getValue($vars),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_octal(&$form, &$var, &$vars)
    {
        return sprintf('<input type="text" size="5" name="%s" value="%s"%s />',
                       $var->getVarName(),
                       sprintf('0%o', octdec($var->getValue($vars))),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_intlist(&$form, &$var, &$vars)
    {
        return sprintf('<input type="text" name="%s" value="%s"%s />',
                       $var->getVarName(),
                       $value = $var->getValue($vars),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_text(&$form, &$var, &$vars)
    {
        $maxlength = $var->type->getMaxLength();
        return sprintf('<input type="text" name="%s" size="%s" value="%s" %s%s%s%s />',
                       $var->getVarName(),
                       $var->type->getSize(),
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, NLS::getCharset()),
                       $this->_genID($var->getVarName()),
                       $var->isDisabled() ? ' disabled="disabled" ' : '',
                       empty($maxlength) ? '' : ' maxlength="' . $maxlength . '"',
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_weatherdotcom(&$form, &$var, &$vars)
    {
        return $this->_renderVarInput_text($form, $var, $vars);
    }

    function _renderVarInput_stringlist(&$form, &$var, &$vars)
    {
        return sprintf('<input type="text" size="60" name="%s" value="%s"%s />',
                       $var->getVarName(),
                       $value = $var->getValue($vars),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_cellphone(&$form, &$var, &$vars)
    {
        return sprintf('<input type="text" name="%s" size="12" value="%s" %s%s%s />',
                       $var->getVarName(),
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, NLS::getCharset()),
                       $this->_genID($var->getVarName()),
                       $var->isDisabled() ? ' disabled="disabled" ' : '',
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_file(&$form, &$var, &$vars)
    {
        $file = $var->getValue($vars);
        return sprintf('<input type="file" size="30" name="%s" value="%s"%s />',
                       $var->getVarName(),
                       $value = $file['name'],
                       $this->_getActionScripts($form, $var));
    }

    /**
     * @todo Show image dimensions in the width/height boxes.
     */
    function _renderVarInput_image(&$form, &$var, &$vars)
    {
        $varname = $var->getVarName();
        $image = $var->getValue($vars);

        /* Check if existing image data is being loaded. */
        $var->type->_loadImageData($image);

        Horde::addScriptFile('image.js', 'horde');
        $graphics_dir = $GLOBALS['registry']->getParam('graphics', 'horde');
        $img_dir = $graphics_dir . '/image';

        $html = '';

        /* Check if there is existing img information stored. */
        if (isset($image['img'])) {
            /* Hidden tag to store the preview image filename. */
            $html = sprintf('<input type="hidden" name="%s" value="%s" %s />',
                   $varname . '[img]',
                   @htmlspecialchars($image['img'], ENT_QUOTES, NLS::getCharset()),
                   $this->_genID($varname . '[img]'));
            /* Unserialize the img information to get the full array. */
            $image['img'] = @unserialize($image['img']);
        }

        /* Output the input tag. */
        if (empty($image['img'])) {
            $js = "var p = document.getElementById('" . $varname . "[preview]'); o = '\\\\'; a = '/'; tmp = '' + document.getElementById('" . $varname . "[new]').value; if (tmp) { while (tmp.indexOf(o) > -1) { pos = tmp.indexOf(o); tmp = '' + (tmp.substring(0, pos) + a + tmp.substring((pos + o.length), tmp.length));}; p.src = 'file:///' + tmp; };";
            $browser = &Browser::singleton();
            if ($browser->isBrowser('msie')) {
                $html .= sprintf('<input type="file" size="30" name="%s" id="%s" onchange="%s" />',
                                 $varname . '[new]',
                                 $varname . '[new]',
                                 $js);
            } else {
                $html .= sprintf('<input type="file" size="30" name="%s" id="%s" onclick="window.setTimeout(\'this.blur();\', 5);" onblur="%s" />',
                                 $varname . '[new]',
                                 $varname . '[new]',
                                 $js);
            }
        } else {
            $html .= sprintf('<input type="file" size="30" name="%s" />',
                             $varname . '[new]');
        }

        /* Output the button to upload/reset the image. */
        if ($var->type->_show_upload) {
            $html .= '&nbsp;';
            $html .= sprintf('<input class="button" name="%s" type="submit" value="%s" /> ',
                             '_do_' . $varname,
                             _("Upload"));
        }

        if (empty($image['img'])) {
            /* No image information stored yet, show a blank
             * preview. */
            $html .= Horde::img('tree/blank.gif', _("Preview"), 'width="50" height="40" align="top" id="' . $varname . '[preview]"', $graphics_dir);
        } else {
            /* Image information stored, show preview, add buttons for
             * image manipulation. */
            $html .= '<br />';
            $img = Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/services/images/view.php');
            if (isset($image['img']['vfs_id'])) {
                /* Calling an image from VFS. */
                $img = Util::addParameter($img, array('f' => $image['img']['vfs_id'],
                                                      's' => 'vfs',
                                                      'p' => $image['img']['vfs_path']));
            } else {
                /* Calling an image from a tmp directory (uploads). */
                $img = Util::addParameter($img, 'f', $image['img']['file']);
            }

            /* Rotate 270. */
            $html .= Horde::link('#', '', '', '', 'showImage(\'' . Util::addParameter($img, array('a' => 'rotate', 'v' => '270')) . '\', \'_p_' . $varname . '\', true);') . Horde::img('rotate-270.png', _("Rotate Left"), 'align="middle"', $img_dir) . '</a>';

            /* Rotate 180. */
            $html .= Horde::link('#', '', '', '', 'showImage(\'' . Util::addParameter($img, array('a' => 'rotate', 'v' => '180')) . '\', \'_p_' . $varname . '\', true);') . Horde::img('rotate-180.png', _("Rotate 180"), 'align="middle"', $img_dir) . '</a>';

            /* Rotate 90. */
            $html .= Horde::link('#', '', '', '', 'showImage(\'' . Util::addParameter($img, array('a' => 'rotate', 'v' => '90')) . '\', \'_p_' . $varname . '\', true);') . Horde::img('rotate-90.png', _("Rotate Right"), 'align="middle"', $img_dir) . '</a>';

            /* Flip image. */
            $html .= Horde::link('#', '', '', '', 'showImage(\'' . Util::addParameter($img, 'a', 'flip') . '\', \'_p_' . $varname . '\', true);') . Horde::img('flip.png', _("Flip"), 'align="middle"', $img_dir) . '</a>';

            /* Mirror image. */
            $html .= Horde::link('#', '', '', '', 'showImage(\'' . Util::addParameter($img, 'a', 'mirror') . '\', \'_p_' . $varname . '\', true);') . Horde::img('mirror.png', _("Mirror"), 'align="middle"', $img_dir) . '</a>';

            /* Apply grayscale. */
            $html .= Horde::link('#', '', '', '', 'showImage(\'' . Util::addParameter($img, 'a', 'grayscale') . '\', \'_p_' . $varname . '\', true);') . Horde::img('grayscale.gif', _("Grayscale"), 'align="middle"', $img_dir) . '</a>';

            /* Resize width. */
            $html .= sprintf('%s<input type="text" size="4" onChange="src=getResizeSrc(\'%s\', \'%s\');showImage(src, \'_p_%s\', true);" %s />',
                   _("w:"),
                   Util::addParameter($img, 'a', 'resize'),
                   $varname,
                   $varname,
                   $this->_genID('_w_' . $varname));

            /* Resize height. */
            $html .= sprintf('%s<input type="text" size="4" onChange="src=getResizeSrc(\'%s\', \'%s\');showImage(src, \'_p_%s\', true);" %s />',
                   _("h:"),
                   Util::addParameter($img, 'a', 'resize'),
                   $varname,
                   $varname,
                   $this->_genID('_h_' . $varname));

            /* Apply fixed ratio resize. */
            $html .= Horde::link('#', '', '', '', 'src=getResizeSrc(\'' . Util::addParameter($img, 'a', 'resize') . '\', \'' . $varname . '\', \'1\');showImage(src, \'_p_' . $varname . '\', true);') . Horde::img('ratio.png', _("Fix ratio"), 'align="middle"', $img_dir) . '</a>';

            /* Keep also original if it has been requested. */
            if ($var->type->_show_keeporig) {
                $html .= sprintf('<input type="checkbox" name="%s"%s />%s' . "\n",
                       $varname . '[keep_orig]',
                       !empty($image['keep_orig']) ? ' checked="checked"' : '',
                       _("Keep original?"));
            }

            /* The preview image element. */
            $html .= '<br /><img src="' . $img . '" ' . $this->_genID('_p_' . $varname) . ">\n";
        }

        return $html;
    }

    function _renderVarInput_longtext(&$form, &$var, &$vars)
    {
        global $browser;

        $id = $this->_genID($var->getVarName(), false);

        $html = sprintf('<textarea id="%s" name="%s" cols="%s" rows="%s"%s>%s</textarea>',
                        $id,
                        $var->getVarName(),
                        $var->type->getCols(),
                        $var->type->getRows(),
                        $this->_getActionScripts($form, $var),
                        $var->getValue($vars));

        if ($var->type->hasHelper('rte') && $browser->hasFeature('rte')) {
            require_once 'Horde/Editor.php';
            $editor = &Horde_Editor::singleton('htmlarea', array('id' => $id));
        }

        if ($var->type->hasHelper() && $browser->hasFeature('javascript')) {
            $html .= '<br /><table border="0" cellpadding="1" cellspacing="0"><tr><td>';
            Horde::addScriptFile('open_html_helper.js', 'horde');
            $imgId = $this->_genID($var->getVarName(), false) . 'ehelper';
            if ($var->type->hasHelper('emoticons')) {
                $html .= Horde::link('', _("Emoticons"), '', '', 'openHtmlHelper(\'emoticons\', \'' . $var->getVarName() . '\'); return false;') . Horde::img('smile.gif', _("Emoticons"), 'id="' . $imgId . '" align="middle"', $GLOBALS['registry']->getParam('graphics', 'horde') . '/emoticons') . '</a>';
            }
            $html .= '</td></tr><tr><td><div ' . $this->_genID('htmlhelper_' . $var->getVarName()) . ' class="control"></div></td></tr></table>' . "\n";
        }

        return $html;
    }

    function _renderVarInput_countedtext(&$form, &$var, &$vars)
    {
        return sprintf('<textarea name="%s" cols="%s" rows="%s"%s>%s</textarea>',
               $var->getVarName(),
               $var->type->getCols(),
               $var->type->getRows(),
               $this->_getActionScripts($form, $var),
               $var->getValue($vars));
    }

    function _renderVarInput_address(&$form, &$var, &$vars)
    {
        return sprintf('<textarea id="%s" name="%s" cols="%s" rows="%s"%s>%s</textarea>',
               $this->_genID($var->getVarName()),
               $var->getVarName(),
               $var->type->getCols(),
               $var->type->getRows(),
               $this->_getActionScripts($form, $var),
               $var->getValue($vars));
    }

    function _renderVarInput_date(&$form, &$var, &$vars)
    {
        $html = sprintf('<input type="text" name="%s" value="%s"%s />',
               $var->getVarName(),
               $value = $var->getValue($vars),
               $this->_getActionScripts($form, $var));
        $html .= '<input type="text" name="' . $var->getVarName() .
                 '" value="' . $var->getValue($vars) . '" />';
        return $html;
    }

    function _renderVarInput_time(&$form, &$var, &$vars)
    {
        return sprintf('<input type="text" size="5" name="%s" value="%s"%s />',
               $var->getVarName(),
               $value = $var->getValue($vars),
               $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_hourminutesecond(&$form, &$var, &$vars)
    {
        $varname = $var->getVarName();
        $time = $var->type->getTimeParts($var->getValue($vars));
        /* Output hours. */
        $hours = array('' => _("HH"));
        for ($i = 0; $i <= 23; $i++) {
            $hours[sprintf('%02d', $i)] = $i;
        }
        $html = sprintf('<select name="%s[hour]" id="%s[hour]"%s>%s</select>',
               $varname,
               $varname,
               $this->_selectOptions($hours, $time['hour']),
               $this->_getActionScripts($form, $var));

        /* Output minutes. */
        $minutes = array('' => _("MM"));
        for ($i = 0; $i <= 59; $i++) {
            $minutes[sprintf('%02d', $i)] = $i;
        }
        $html .= sprintf('<select name="%s[minute]" id="%s[minute]"%s>%s</select>',
               $varname,
               $varname,
               $this->_selectOptions($minutes, $time['minute']),
               $this->_getActionScripts($form, $var));

        /* Return if seconds are not required. */
        if (!$var->type->_show_seconds) {
            return $html;
        }

        /* Output seconds. */
        $seconds = array('' => _("SS"));
        for ($i = 0; $i <= 59; $i++) {
            $seconds[sprintf('%02d', $i)] = $i;
        }
        $html .= sprintf('<select name="%s[second]" id="%s[second]"%s>%s</select>',
               $varname,
               $varname,
               $this->_getActionScripts($form, $var),
               $this->_selectOptions($seconds, $time['second']));
        return $html;
    }

    function _renderVarInput_monthyear(&$form, &$var, &$vars)
    {
        $dates = array();
        $dates['month'] = array('' => _("MM"),
                        1 => _("January"),
                        2 => _("February"),
                        3 => _("March"),
                        4 => _("April"),
                        5 => _("May"),
                        6 => _("June"),
                        7 => _("July"),
                        8 => _("August"),
                        9 => _("September"),
                        10 => _("October"),
                        11 => _("November"),
                        12 => _("December"));
        $dates['year'] = array('' => _("YYYY"));
        if ($var->type->_start_year > $var->type->_end_year) {
            for ($i = $var->type->_start_year; $i >= $var->type->_end_year; $i--) {
                $dates['year'][$i] = $i;
            }
        } else {
            for ($i = $var->type->_start_year; $i <= $var->type->_end_year; $i++) {
                $dates['year'][$i] = $i;
            }
        }
        $html = sprintf('<select name="%s"%s>%s</select>',
               $var->type->getMonthVar($var),
               $this->_getActionScripts($form, $var),
               $this->_selectOptions($dates['month'], $vars->get($var->type->getMonthVar($var))));
        $html .= sprintf('<select name="%s"%s>%s</select>',
               $var->type->getYearVar($var),
               $this->_getActionScripts($form, $var),
               $this->_selectOptions($dates['year'], $vars->get($var->type->getYearVar($var))));
        return $html;
    }

    function _renderVarInput_monthdayyear(&$form, &$var, &$vars)
    {
        $dates = array();
        $dates['month'] = array(''   => _("MM"),
                        '1'  => _("January"),
                        '2'  => _("February"),
                        '3'  => _("March"),
                        '4'  => _("April"),
                        '5'  => _("May"),
                        '6'  => _("June"),
                        '7'  => _("July"),
                        '8'  => _("August"),
                        '9'  => _("September"),
                        '10' => _("October"),
                        '11' => _("November"),
                        '12' => _("December"));
        $dates['day'] = array('' => _("DD"));
        for ($i = 1; $i <= 31; $i++) {
            $dates['day'][$i] = $i;
        }
        $dates['year'] = array('' => _("YYYY"));
        if ($var->type->_start_year > $var->type->_end_year) {
            for ($i = $var->type->_start_year; $i >= $var->type->_end_year; $i--) {
                $dates['year'][$i] = $i;
            }
        } else {
            for ($i = $var->type->_start_year; $i <= $var->type->_end_year; $i++) {
                $dates['year'][$i] = $i;
            }
        }
        $date = $var->type->getDateParts($var->getValue($vars));

        // TODO: use NLS to get the order right for the Rest Of The
        // World.
        $html = '';
        $date_parts = array('month', 'day', 'year');
        foreach ($date_parts as $part) {
            $varname = $var->getVarName() . '[' . $part . ']';
            $html .= sprintf('<select name="%s" id="%s"%s>%s</select>',
                   $varname,
                   $varname,
                   $this->_getActionScripts($form, $var),
                   $this->_selectOptions($dates[$part], $date[$part]));
        }

        if ($var->type->_picker && $GLOBALS['browser']->hasFeature('javascript')) {
            Horde::addScriptFile('open_calendar.js', 'horde');
            $imgId = $this->_genID($var->getVarName(), false) . 'goto';
            $html .= '<div id="goto" class="headerbox" style="position:absolute;visibility:hidden;padding:0px;"></div>';
            $html .= Horde::link('', _("Select a date"), '', '', 'openCalendar(\'' . $imgId . '\', \'' . $var->getVarName() . '\'); return false;') . Horde::img('calendar.gif', _("Calendar"), 'id="' . $imgId . '" align="middle"', $GLOBALS['registry']->getParam('graphics', 'horde')) . "</a>\n";
        }
        return $html;
    }

    function _renderVarInput_colorpicker(&$form, &$var, &$vars)
    {
        global $registry, $browser;

        $html = '<table border="0" cellpadding="0" cellspacing="0"><tr><td>' .
                '<input type="text" size="10" maxlength="7" name="' .
                $var->getVarName() . '" id="' . $var->getVarName() .
                '" value="' . $var->getValue($vars) . '" /></td>';
        if ($browser->hasFeature('javascript')) {
            Horde::addScriptFile('open_colorpicker.js', 'horde');
            $html .= '<td width="20" id="colordemo_' . $var->getVarName() . '" style="background-color:' . $var->getValue($vars) . '"> </td>';
            $html .= '<td>' . Horde::link('#', _("Color Picker"), 'widget', '', 'openColorPicker(\'' . $var->getVarName() . '\'); return false;') . Horde::img('colorpicker.gif', _("Color Picker"), 'height="16"', $registry->getParam('graphics', 'horde')) . '</a></td>';
            $html .= '<td><div id="colorpicker_' . $var->getVarName() . '" class="control"></div></td>';
        }
        $html .= '</tr></table>';
        return $html;
    }

    function _renderVarInput_sorter(&$form, &$var, &$vars)
    {
        global $registry;

        $varname = $var->getVarName();
        $instance = $var->type->_instance;

        Horde::addScriptFile('sorter.js', 'horde');

        $html = '<input type="hidden" name="' . $varname .
                '[array]" value="" ' . $this->_genID($varname . '[array]') .
                ' /><table border="0" cellpadding="0" cellspacing="0"><tr>' .
                '<td><select multiple="multiple" size="' .
                $var->type->getSize() . '" name="' . $varname .
                '[list]" onchange="' . $instance . '.deselectHeader();" ' .
                $this->_genID($varname . '[list]') . '>';
        $html .= $var->type->getOptions() . '</select></td><td>';
        $html .= Horde::link('#', _("Move up"), '', '', $instance . '.moveColumnUp(); return false;') . Horde::img('nav/up.gif', _("Move up"), '', $registry->getParam('graphics', 'horde')) . '</a><br />';
        $html .= Horde::link('#', _("Move up"), '', '', $instance . '.moveColumnDown(); return false;') . Horde::img('nav/down.gif', _("Move down"), '', $registry->getParam('graphics', 'horde')) . '</a></td></tr></table>';
        $html .= '<script language="JavaScript" type="text/javascript">' . "\n";
        $html .= sprintf('%1$s = new Horde_Form_Sorter(\'%1$s\', \'%2$s\', \'%3$s\');' . "\n",
               $instance, $varname, $var->type->getHeader());

        $html .= sprintf("%s.setHidden();\n</script>\n", $instance);
        return $html;
    }

    function _renderVarInput_invalid(&$form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_invalid($form, $var, $vars);
    }

    function _renderVarInput_enum(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        $prompt = $var->type->getPrompt();
        if (!empty($prompt)) {
            $prompt = '<option value="">' . @htmlspecialchars($prompt, ENT_QUOTES, NLS::getCharset()) . '</option>';
        }
        return sprintf('<select name="%s" %s%s>%s%s</select>',
               $var->getVarName(),
               $this->_genID($var->getVarName()),
               $this->_getActionScripts($form, $var),
               $prompt,
               $this->_selectOptions($values, $var->getValue($vars)));
    }

    function _renderVarInput_mlenum(&$form, &$var, &$vars)
    {
        $varname = $var->getVarName();
        $values = $var->getValues();
        $prompts = $var->type->getPrompts();
        $selected = $var->getValue($vars);
        /* If passing a non-array value need to get the keys. */
        if (!is_array($selected)) {
            foreach ($values as $key_1 => $values_2) {
                if (isset($values_2[$selected])) {
                    $selected = array('1' => $key_1, '2' => $selected);
                    break;
                }
            }
        }

        /* Hidden tag to store the current first level. */
        $html = sprintf('<input type="hidden" name="%s[old]" value="%s" %s />',
               $varname,
               @htmlspecialchars($selected['1'], ENT_QUOTES, NLS::getCharset()),
               $this->_genID($varname . '[old]'));

        /* First level. */
        require_once 'Horde/Array.php';
        $values_1 = Horde_Array::valuesToKeys(array_keys($values));
        $html .= sprintf('<select %s name="%s[1]"%s>',
               $this->_genID($varname . '[1]'),
               $varname,
               ($var->hasAction() ? ' ' . $this->_genActionScript($form, $var->_action, $varname) : ''));
        if (!empty($prompts)) {
            $html .= '<option value="">' . @htmlspecialchars($prompts[0], ENT_QUOTES, NLS::getCharset()) . '</option>';
        }
        $html .= $this->_selectOptions($values_1, $selected['1']);
        $html .= '</select>';

        /* Second level. */
        $html .= sprintf('<select %s name="%s[2]"%s>',
                         $this->_genID($varname . '[2]'),
                         $varname,
                         ($var->hasAction() ? ' ' . $this->_genActionScript($form, $var->_action, $varname) : ''));
        if (!empty($prompts)) {
            $html .= '<option value="">' . @htmlspecialchars($prompts[1], ENT_QUOTES, NLS::getCharset()) . '</option>';
        }
        $values_2 = array();
        if (!empty($selected['1'])) {
            $values_2 = &$values[$selected['1']];
        }
        $html .= $this->_selectOptions($values_2, $selected['2']);
        $html .= '</select>';
        return $html;
    }

    function _renderVarInput_multienum(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        $selected = $vars->getExists($var->getVarName(), $wasset);
        if (!$wasset) {
            $selected = $var->getDefault();
        }
        $html = sprintf('<select multiple="multiple" size="%s" name="%s[]" %s>%s</select>',
               $var->type->size,
               $var->getVarName(),
               $this->_getActionScripts($form, $var),
               $this->_multiSelectOptions($values, $selected));
        $html .= "<br />\n" . _("To select multiple items, hold down the Control (PC) or Command (Mac) key while clicking.") . "\n";
        return $html;
    }

    function _renderVarInput_radio(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        $value  = $var->getValue($vars);
        $actions = $this->_getActionScripts($form, $var);
        return $this->_radioButtons($var->getVarName(), $values, $value, $actions);
    }

    function _renderVarInput_set(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        $value  = $var->getValue($vars);
        $actions = $this->_getActionScripts($form, $var);
        return $this->_checkBoxes($var->getVarName(), $values, $value, $actions);
    }

    function _renderVarInput_link(&$form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_link($form, $var, $vars);
    }

    function _renderVarInput_email(&$form, &$var, &$vars)
    {
        return sprintf('<input type="text" name="%s" value="%s"%s />',
               $var->getVarName(),
               $value = $var->getValue($vars),
               $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_matrix(&$form, &$var, &$vars)
    {
        $varname   = $var->getVarName();
        $var_array = $var->getValue($vars);
        $cols      = $var->type->getCols();
        $rows      = $var->type->getRows();
        $matrix    = $var->type->getMatrix();
        $new_input = $var->type->getNewInput();

        $html = '<table border="0" cellpadding="0" cellspacing="0"><tr>';

        $html .= '<td align="right" width="20%"></td>';
        foreach ($cols as $col_title) {
            $html .= sprintf('<td align="center" width="1%%">%s</td>', $col_title);
        }
        $html .= '<td align="right" width="60%"></td></tr>';

        /* Offer a new row of data to be added to the matrix? */
        if ($new_input) {
            $html .= '<tr><td>';
            if (is_array($new_input)) {
                $html .= sprintf('<select %s name="%s[n][r]"><option value="">%s</option>%s</select><br />',
                       $this->_genID($varname . '[n][r]'),
                       $varname,
                       _("-- select --"),
                       $this->_selectOptions($new_input, $var_array['n']['r']));
            } elseif ($new_input == true) {
                $html .= sprintf('<input %s type="text" name="%s[n][r]" value="%s" />',
                       $this->_genID($varname . '[n][r]'),
                       $varname,
                       $var_array['n']['r']);
            }
            $html .= ' </td>';
            foreach ($cols as $col_id => $col_title) {
                $html .= sprintf('<td align="center"><input type="checkbox" name="%s[n][v][%s]" /></td>', $varname, $col_id);
            }
            $html .= '<td> </td></tr>';
        }

        /* Loop through the rows and create checkboxes for each column. */
        foreach ($rows as $row_id => $row_title) {
            $html .= sprintf('<tr><td>%s</td>', $row_title);
            foreach ($cols as $col_id => $col_title) {
                $html .= sprintf('<td align="center"><input type="checkbox" name="%s[r][%s][%s]"%s /></td>', $varname, $row_id, $col_id, (!empty($matrix[$row_id][$col_id]) ? ' checked="checked"' : ''));
            }
            $html .= '<td> </td></tr>';
        }

        $html .= '</table>';
        return $html;
    }

    function _renderVarInput_password(&$form, &$var, &$vars)
    {
        return sprintf('<input type="password" name="%s" value="%s"%s />',
               $var->getVarName(),
               $value = $var->getValue($vars),
               $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_emailconfirm(&$form, &$var, &$vars)
    {
        $email = $var->getValue($vars);
        $html = sprintf('<input type="text" name="%s[original]" value="%s"%s />',
               $var->getVarName(),
               $value = $email['original'],
               $this->_getActionScripts($form, $var));
        $html .= sprintf('<input type="text" name="%s[confirm]" value="%s"%s />',
               $var->getVarName(),
               $value = $email['confirm'],
               $this->_getActionScripts($form, $var));
        return $html;
    }

    function _renderVarInput_passwordconfirm(&$form, &$var, &$vars)
    {
        $password = $var->getValue($vars);
        $html = sprintf('<input type="password" name="%s[original]" value="%s"%s />',
               $var->getVarName(),
               $value = $password['original'],
               $this->_getActionScripts($form, $var));
        $html .= sprintf('<input type="password" name="%s[confirm]" value="%s"%s />',
               $var->getVarName(),
               $value = $password['confirm'],
               $this->_getActionScripts($form, $var));
        return $html;
    }

    function _renderVarInput_boolean(&$form, &$var, &$vars)
    {
        $varName = $var->getVarName();

        $html = '<input type="checkbox" name="' .  $varName . '"' .
                ($var->getValue($vars) ? ' checked="checked"' : '');
        if ($var->hasAction()) {
            $html .= $this->_genActionScript($form, $var->_action,
                                             $var->getVarName());
        }
        $html .= ' />';
        return $html;
    }

    function _renderVarInput_creditcard(&$form, &$var, &$vars)
    {
        $html = '<input type="text" name="' . $var->getVarName() . '"' .
                $var->getValue($vars);
        if ($var->hasAction()) {
            $html .= $this->_genActionScript($form, $var->_action,
                                             $var->getVarName());
        }
        $html .= ' />';
        return $html;
    }

    function _renderVarDisplayDefault(&$form, &$var, &$vars)
    {
        return nl2br(@htmlspecialchars($var->getValue($vars), ENT_QUOTES, NLS::getCharset()));
    }

    function _renderVarDisplay_html(&$form, &$var, &$vars)
    {
        return $var->getValue($vars);
    }

    function _renderVarDisplay_email(&$form, &$var, &$vars)
    {
        $email = $var->getValue($vars);

        if ($var->type->_strip_domain && strstr($email, '@')) {
            $email = str_replace(array('@', '.'),
                                 array(' (at) ', ' (dot) '),
                                 $email);
        }

        return nl2br(@htmlspecialchars($email, ENT_QUOTES, NLS::getCharset()));
    }

    function _renderVarDisplay_password(&$form, &$var, &$vars)
    {
        return '********';
    }

    function _renderVarDisplay_passwordconfirm(&$form, &$var, &$vars)
    {
        return '********';
    }

    function _renderVarDisplay_octal(&$form, &$var, &$vars)
    {
        return sprintf('0%o', octdec($var->getValue($vars)));
    }

    function _renderVarDisplay_boolean(&$form, &$var, &$vars)
    {
        return $var->getValue($vars) == 'on' ? _("On") : _("Off");
    }

    function _renderVarDisplay_enum(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        $value = $var->getValue($vars);
        if (count($values) == 0) {
            return _("No values");
        } elseif (isset($values[$value]) && $value != '') {
            return @htmlspecialchars($values[$value], ENT_QUOTES, NLS::getCharset());
        }
    }

    function _renderVarDisplay_radio(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        if (count($values) == 0) {
            return _("No values");
        } elseif (isset($values[$var->getValue($vars)])) {
            return @htmlspecialchars($values[$var->getValue($vars)], ENT_QUOTES, NLS::getCharset());
        }
    }

    function _renderVarDisplay_multienum(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        $on = $var->getValue($vars);
        if (!count($values) || !count($on)) {
            return _("No values");
        } else {
            $display = array();
            foreach ($values as $value => $name) {
                if (in_array($value, $on)) {
                    $display[] = $name;
                }
            }
            return @htmlspecialchars(implode(', ', $display), ENT_QUOTES, NLS::getCharset());
        }
    }

    function _renderVarDisplay_set(&$form, &$var, &$vars)
    {
        $values = $var->getValues();
        $on = $var->getValue($vars);
        if (!count($values) || !count($on)) {
            return _("No values");
        } else {
            $display = array();
            foreach ($values as $value => $name) {
                if (in_array($value, $on)) {
                    $display[] = $name;
                }
            }
            return @htmlspecialchars(implode(', ', $display), ENT_QUOTES, NLS::getCharset());
        }
    }

    function _renderVarDisplay_image(&$form, &$var, &$vars)
    {
        $img_params = $var->getValue($vars);
        $img_url = Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/services/images/view.php');
        $img_url = Util::addParameter($img_url, $img_params);
        return Horde::img($img_url, $img_params['f'], '', '');
    }

    function _renderVarDisplay_cellphone(&$form, &$var, &$vars)
    {
        global $registry;
        $number = $var->getValue($vars);

        $html = $number;

        if ($registry->applications['swoosh']['status'] != 'inactive') {
            $url = Horde::url($registry->getParam('webroot', 'swoosh') . '/send.php');
            $url = Util::addParameter($url, 'to', $number);
            $html .= '&nbsp;' . Horde::link($url, _("Send SMS")) . Horde::img('swoosh.gif', _("Send SMS"), 'align="middle"', $registry->getParam('graphics', 'swoosh')) . '</a>';
        }
        return $html;
    }

    function _renderVarDisplay_address(&$form, &$var, &$vars)
    {
        $address = $var->getValue($vars);

        if (preg_match('/(.*)\n(.*)\s*,\s*(\w+)\.?\s+(\d+|[a-zA-Z]\d[a-zA-Z]\s?\d[a-zA-Z]\d)/', $address, $addressParts)) {
            /* American/Canadian address style. */
            /* Mapquest generated map */
            $mapurl = 'http://www.mapquest.com/maps/map.adp?size=big&zoom=7';
            if (!empty($addressParts[1])) {
                $mapurl .= '&address=' . urlencode($addressParts[1]);
            }
            if (!empty($addressParts[2])) {
                $mapurl .= '&city=' . urlencode($addressParts[2]);
            }
            if (!empty($addressParts[3])) {
                $mapurl .= '&state=' . urlencode($addressParts[3]);
            }
            if (!empty($addressParts[4])) {
                $mapurl .= '&zipcode=' . urlencode($addressParts[4]);
                if (preg_match('|[a-zA-Z]\d[a-zA-Z]\s?\d[a-zA-Z]\d|', $addressParts[4])) {
                    $mapurl .= '&country=CA';
                }
            }

            /* Yahoo! generated map. */
            $mapurl2 = 'http://us.rd.yahoo.com/maps/home/submit_a/*-http://maps.yahoo.com/maps?srchtype=a&getmap=Get+Map&';
            if (!empty($addressParts[1])) {
                $mapurl2 .= '&addr=' . urlencode($addressParts[1]);
            }
            if (!empty($addressParts[2]) && !empty($addressParts[3])) {
                $mapurl2 .= '&csz=' . urlencode($addressParts[2] . ' ' . $addressParts[3]);
            }
            if ((empty($addressParts[2]) || empty($addressParts[3])) && !empty($addressParts[4])) {
                $mapurl2 .= '&csz=' . urlencode($addressParts[4]);
                if (preg_match('|[a-zA-Z]\d[a-zA-Z]\s?\d[a-zA-Z]\d|', $addressParts[4])) {
                    $mapurl2 .= '&country=ca';
                }
            }
        } elseif (preg_match('/(.*)\nD-(\d{5})\s+(.*)/i', $address, $addressParts)) {
            /* German address style. */
            $mapurl = 'http://www.map24.de/map24/index.php3?maptype=RELOAD&country0=de&gcf=1';
            if (!empty($addressParts[1])) {
                $mapurl .= '&street0=' . urlencode($addressParts[1]);
            }
            if (!empty($addressParts[2])) {
                $mapurl .= '&zip0=' . urlencode($addressParts[2]);
            }
            if (!empty($addressParts[3])) {
                $mapurl .= '&city0=' . urlencode($addressParts[3]);
            }
        }
        $html = nl2br(@htmlspecialchars($var->getValue($vars), ENT_QUOTES, NLS::getCharset()));
        if (!empty($mapurl)) {
            global $registry;
            $html .= Horde::link($mapurl, _("Mapquest map"), null, '_blank') . Horde::img('map.gif', _("Mapquest map"), 'align="middle"', $registry->getParam('graphics', 'horde')) . '</a>';
        }
        if (!empty($mapurl2)) {
            $html .= Horde::link($mapurl2, _("Yahoo! map"), null, '_blank') . Horde::img('map.gif', _("Yahoo! map"), 'align="middle"', $registry->getParam('graphics', 'horde')) . '</a>';
        }
        return $html;
    }

    function _renderVarDisplay_date(&$form, &$var, &$vars)
    {
        return $var->type->getFormattedTimeFull($var->getValue($vars));
    }

    function _renderVarDisplay_monthyear(&$form, &$var, &$vars)
    {
        return $vars->get($var->getVarName() . '[month]') . ', ' . $vars->get($var->getVarName() . '[year]');
    }

    function _renderVarDisplay_monthdayyear(&$form, &$var, &$vars)
    {
        $date = $var->getValue($vars);
        if ((is_array($date) && !empty($date['year']) && !empty($date['month']) && !empty($date['day'])) || (!is_array($date) && !empty($date))) {
            return $var->type->formatDate($date);
        }
        return '';
    }

    function _renderVarDisplay_invalid(&$form, &$var, &$vars)
    {
        return '<span class="form-error">' . @htmlspecialchars($var->type->message, ENT_QUOTES, NLS::getCharset()) . '</span>';
    }

    function _renderVarDisplay_link(&$form, &$var, &$vars)
    {
        $html = '';
        if (isset($var->type->values[0]) && is_array($var->type->values[0])) {
            $count = count($var->type->values);
            for ($i = 0; $i < $count; $i++) {
                if (empty($var->type->values[$i]['url']) || empty($var->type->values[$i]['text'])) {
                    continue;
                }
                if ($i > 0) {
                    $html .= ' | ';
                }
                $html .= Horde::link($var->type->values[$i]['url'], $var->type->values[$i]['text'], 'widget') . $var->type->values[$i]['text'] . '</a>';
            }
        } else {
            if (empty($var->type->values['url']) || empty($var->type->values['text'])) {
                return $html;
            }
            $html .= Horde::link($var->type->values['url'], $var->type->values['text'], 'widget') . $var->type->values['text'] . '</a>';
        }
        return $html;
    }

    function _selectOptions(&$values, $selectedValue = false)
    {
        $result = '';
        $sel = false;
        foreach ($values as $value => $display) {
            if (!is_null($selectedValue) && !$sel && $value == $selectedValue) {
                $selected = ' selected="selected"';
                $sel = true;
            } else {
                $selected = '';
            }
            $result .= ' <option value="' . @htmlspecialchars($value, ENT_QUOTES, NLS::getCharset()) . '"' . $selected . '>' . htmlspecialchars($display) . "</option>\n";
        }

        return $result;
    }

    function _multiSelectOptions(&$values, $selectedValues)
    {
        $result = '';
        $sel = false;
        foreach ($values as $value => $display) {
            if (@in_array($value, $selectedValues)) {
                $selected = ' selected="selected"';
            } else {
                $selected = '';
            }
            $result .= " <option value=\"" . @htmlspecialchars($value, ENT_QUOTES, NLS::getCharset()) . "\"$selected>" . htmlspecialchars($display) . "</option>\n";
        }

        return $result;
    }

    function _checkBoxes($name, $values, $checkedValues, $actions = '')
    {
        $result = '';
        if (!is_array($checkedValues)) {
            $checkedValues = array();
        }
        $i = 0;
        foreach ($values as $value => $display) {
            $checked = (in_array($value, $checkedValues)) ? ' checked="checked"' : '';
            $result .= sprintf('<input id="%s%s" type="checkbox" name="%s[]" value="%s"%s%s /><label for="%s%s">&nbsp;%s</label><br />',
                               $name,
                               $i,
                               $name,
                               $value,
                               $checked,
                               $actions,
                               $name,
                               $i,
                               $display);
            $i++;
        }

        return $result;
    }

    function _radioButtons($name, $values, $checkedValue = null, $actions = '')
    {
        $result = '';
        $i = 0;
        foreach ($values as $value => $display) {
            $checked = (!is_null($checkedValue) && $value == $checkedValue) ? ' checked="checked"' : '';
            $result .= sprintf('<input id="%s%s" type="radio" name="%s" value="%s"%s%s /><label for="%s%s">&nbsp;%s</label><br />',
                               $name,
                               $i,
                               $name,
                               $value,
                               $checked,
                               $actions,
                               $name,
                               $i,
                               $display);
            $i++;
        }

        return $result;
    }

    function _genID($name, $fulltag = true)
    {
        return $fulltag ? 'id="' . @htmlspecialchars($name, ENT_QUOTES, NLS::getCharset()) . '"' : $name;
    }

    function _genActionScript(&$form, $action, $varname)
    {
        $html = '';
        $triggers = $action->getTrigger();
        if (!is_array($triggers)) {
            $triggers = array($triggers);
        }
        $js = $action->getActionScript($form, $this, $varname);
        foreach ($triggers as $trigger) {
            if ($trigger == 'onload') {
                $this->_addOnLoadJavascript($js);
            } else {
                $html .= ' ' . $trigger . '="' . $js . '"';
            }
        }
        return $html;
    }

    function _getActionScripts(&$form, &$var)
    {
        $actions = '';
        if ($var->hasAction()) {
            $varname = $var->getVarName();
            $action =& $var->_action;
            $triggers = $action->getTrigger();
            if (!is_array($triggers)) {
                $triggers = array($triggers);
            }
            $js = $action->getActionScript($form, $this, $varname);
            foreach ($triggers as $trigger) {
                if ($trigger == 'onload') {
                    $this->_addOnLoadJavascript($js);
                } else {
                    $actions .= ' ' . $trigger . '="' . $js . '"';
                }
            }
        }
        return $actions;
    }

    function _addOnLoadJavascript($script)
    {
        $this->_onLoadJS[] = $script;
    }

    function renderEnd()
    {
        if (count($this->_onLoadJS)) {
            return "<script language=\"JavaScript\" type=\"text/javascript\">" .
                "<!--\n" .  implode("\n", $this->_onLoadJS) . "\n// -->\n" .
                "</script>";
        } else {
            return '';
        }
    }

}

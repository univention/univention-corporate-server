<?php
/**
 * The Horde_UI_VarRenderer_html:: class renders variables to HTML.
 *
 * $Horde: framework/UI/UI/VarRenderer/html.php,v 1.98.2.42 2009-09-14 07:22:07 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (LGPL).
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_VarRenderer_html extends Horde_UI_VarRenderer {

    var $_onLoadJS = array();

    function _renderVarInputDefault($form, &$var, &$vars)
    {
        return '<strong>Warning:</strong> Unknown variable type ' .
            @htmlspecialchars($var->getTypeName(), ENT_QUOTES, $this->_charset);
    }

    function _renderVarInput_number($form, &$var, &$vars)
    {
        $value = $var->getValue($vars);
        if ($var->type->getProperty('fraction')) {
            $value = sprintf('%01.' . $var->type->getProperty('fraction') . 'f', $value);
        }
        $linfo = NLS::getLocaleInfo();
        /* Only if there is a mon_decimal_point do the
         * substitution. */
        if (!empty($linfo['mon_decimal_point'])) {
            $value = str_replace('.', $linfo['mon_decimal_point'], $value);
        }
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" size="5" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       $value,
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_int($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" size="5" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_octal($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" size="5" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       sprintf('0%o', octdec($var->getValue($vars))),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_intlist($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_text($form, &$var, &$vars)
    {
        $maxlength = $var->type->getMaxLength();
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s" id="%s" size="%s" value="%s" %s%s%s />',
                       $varname,
                       $varname,
                       $var->type->getSize(),
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $var->isDisabled() ? ' disabled="disabled" ' : '',
                       empty($maxlength) ? '' : ' maxlength="' . $maxlength . '"',
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_stringlist($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" size="60" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_stringarray($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" size="60" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars(implode(', ', $var->getValue($vars)), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_phone($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s" id="%s" size="15" value="%s" %s%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $var->isDisabled() ? ' disabled="disabled" ' : '',
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_cellphone($form, &$var, &$vars)
    {
        return $this->_renderVarInput_phone($form, $var, $vars);
    }

    function _renderVarInput_ipaddress($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s" id="%s" size="16" value="%s" %s%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $var->isDisabled() ? ' disabled="disabled" ' : '',
                       $this->_getActionScripts($form, $var)
               );
    }

    function _renderVarInput_file($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="file" size="30" name="%s" id="%s"%s />',
                       $varname,
                       $varname,
                       $this->_getActionScripts($form, $var));
    }

    /**
     * @todo Show image dimensions in the width/height boxes.
     */
    function _renderVarInput_image($form, &$var, &$vars)
    {
        $varname = htmlspecialchars($var->getVarName());
        $image = $var->type->getImage($vars, $var);

        Horde::addScriptFile('image.js', 'horde', true);
        $graphics_dir = $GLOBALS['registry']->getImageDir('horde');
        $img_dir = $graphics_dir . '/image';

        $html = '';

        /* Check if there is existing img information stored. */
        if (isset($image['img'])) {
            /* Hidden tag to store the preview image id. */
            $html = sprintf('<input type="hidden" name="%s" id="%s" value="%s" />',
                            $varname . '[hash]',
                            $varname . '[hash]',
                            $var->type->getRandomId());
        }

        /* Output MAX_FILE_SIZE parameter to limit large files. */
        if ($var->type->getProperty('max_filesize')) {
            $html .= sprintf('<input type="hidden" name="MAX_FILE_SIZE" value="%d" />',
                             $var->type->getProperty('max_filesize'));
        }

        /* Output the input tag. */
        if (empty($image['img'])) {
            $js = "var p = document.getElementById('" . $varname . "[preview]'); o = '\\\\'; a = '/'; tmp = '' + document.getElementById('" . $varname . "[new]').value; if (tmp) { while (tmp.indexOf(o) > -1) { pos = tmp.indexOf(o); tmp = '' + (tmp.substring(0, pos) + a + tmp.substring((pos + o.length), tmp.length));}; p.src = 'file:///' + tmp; p.alt = '" . addslashes(_("If you see this message but no image, the image you want to upload can't be displayed by your browser.")) . "'; };";
            $browser = &Browser::singleton();
            if ($browser->isBrowser('msie')) {
                $html .= sprintf('<input type="file" size="30" name="%s" id="%s" onchange="%s" />',
                                 $varname . '[new]',
                                 $varname . '[new]',
                                 $js);
            } else {
                $html .= sprintf('<input type="file" size="30" name="%s" id="%s" onclick="window.setTimeout(\'document.getElementById(\\\'%s\\\').blur();\', 5);" onblur="%s" />',
                                 $varname . '[new]',
                                 $varname . '[new]',
                                 $varname . '[new]',
                                 $js);
            }
        } else {
            $html .= sprintf('<input type="file" size="30" name="%s" id="%s" />',
                             $varname . '[new]',
                             $varname . '[new]');
        }

        /* Output the button to upload/reset the image. */
        if ($var->type->getProperty('show_upload')) {
            $html .= '&nbsp;';
            $html .= sprintf('<input class="button" name="%s" id="%s" type="submit" value="%s" /> ',
                             '_do_' . $varname,
                             '_do_' . $varname,
                             _("Upload"));
        }

        if (empty($image['img'])) {
            /* No image information stored yet, show a blank preview. */
            $html .= Horde::img('tree/blank.png', _("Preview"), 'width="50" height="40" id="' . $varname . '[preview]"', $graphics_dir);
        } else {
            /* Image information stored, show preview, add buttons for image
             * manipulation. */
            $html .= '<br />';
            $img = Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/images/view.php');
            if (isset($image['img']['vfs_id'])) {
                /* Calling an image from VFS. */
                $img = Util::addParameter($img, array('f' => $image['img']['vfs_id'],
                                                      's' => 'vfs',
                                                      'p' => $image['img']['vfs_path']));
            } else {
                /* Calling an image from a tmp directory (uploads). */
                $img = Util::addParameter($img, 'f', $image['img']['file']);
            }

            /* Reset. */
            $html .= Horde::link('#', _("Reset"), '', '', 'showImage(\'' . $img . '\', \'_p_' . $varname . '\', true);') . Horde::img('refresh.png', _("Reset"), '', $img_dir) . '</a>';

            /* Rotate 270. */
            $html .= Horde::link('#', _("Rotate Left"), '', '', 'showImage(\'' . Util::addParameter($img, array('a' => 'rotate', 'v' => '270')) . '\', \'_p_' . $varname . '\', true);') . Horde::img('rotate-270.png', _("Rotate Left"), '', $img_dir) . '</a>';

            /* Rotate 180. */
            $html .= Horde::link('#', _("Rotate 180"), '', '', 'showImage(\'' . Util::addParameter($img, array('a' => 'rotate', 'v' => '180')) . '\', \'_p_' . $varname . '\', true);') . Horde::img('rotate-180.png', _("Rotate 180"), '', $img_dir) . '</a>';

            /* Rotate 90. */
            $html .= Horde::link('#', _("Rotate Right"), '', '', 'showImage(\'' . Util::addParameter($img, array('a' => 'rotate', 'v' => '90')) . '\', \'_p_' . $varname . '\', true);') . Horde::img('rotate-90.png', _("Rotate Right"), '', $img_dir) . '</a>';

            /* Flip image. */
            $html .= Horde::link('#', _("Flip"), '', '', 'showImage(\'' . Util::addParameter($img, 'a', 'flip') . '\', \'_p_' . $varname . '\', true);') . Horde::img('flip.png', _("Flip"), '', $img_dir) . '</a>';

            /* Mirror image. */
            $html .= Horde::link('#', _("Mirror"), '', '', 'showImage(\'' . Util::addParameter($img, 'a', 'mirror') . '\', \'_p_' . $varname . '\', true);') . Horde::img('mirror.png', _("Mirror"), '', $img_dir) . '</a>';

            /* Apply grayscale. */
            $html .= Horde::link('#', _("Grayscale"), '', '', 'showImage(\'' . Util::addParameter($img, 'a', 'grayscale') . '\', \'_p_' . $varname . '\', true);') . Horde::img('grayscale.png', _("Grayscale"), '', $img_dir) . '</a>';

            /* Resize width. */
            $html .= sprintf('%s<input type="text" size="4" onchange="src=getResizeSrc(\'%s\', \'%s\');showImage(src, \'_p_%s\', true);" %s />',
                   _("w:"),
                   Util::addParameter($img, 'a', 'resize'),
                   $varname,
                   $varname,
                   $this->_genID('_w_' . $varname));

            /* Resize height. */
            $html .= sprintf('%s<input type="text" size="4" onchange="src=getResizeSrc(\'%s\', \'%s\');showImage(src, \'_p_%s\', true);" %s />',
                   _("h:"),
                   Util::addParameter($img, 'a', 'resize'),
                   $varname,
                   $varname,
                   $this->_genID('_h_' . $varname));

            /* Apply fixed ratio resize. */
            $html .= Horde::link('#', _("Fix ratio"), '', '', 'src=getResizeSrc(\'' . Util::addParameter($img, 'a', 'resize') . '\', \'' . $varname . '\', \'1\');showImage(src, \'_p_' . $varname . '\', true);') . Horde::img('ratio.png', _("Fix ratio"), '', $img_dir) . '</a>';

            /* Keep also original if it has been requested. */
            if ($var->type->getProperty('show_keeporig')) {
                $html .= sprintf('<input type="checkbox" class="checkbox" name="%s" id="%s"%s />%s' . "\n",
                                 $varname . '[keep_orig]',
                                 $varname . '[keep_orig]',
                                 !empty($image['keep_orig']) ? ' checked="checked"' : '',
                                 _("Keep original?"));
            }

            /* The preview image element. */
            $html .= '<br /><img src="' . $img . '" ' . $this->_genID('_p_' . $varname) . ">\n";
        }

        return $html;
    }

    function _renderVarInput_longtext($form, &$var, &$vars)
    {
        global $browser;

        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $html = sprintf('<textarea id="%s" name="%s" cols="%s" rows="%s"%s%s>%s</textarea>',
                        $varname,
                        $varname,
                        (int)$var->type->getCols(),
                        (int)$var->type->getRows(),
                        $this->_getActionScripts($form, $var),
                        $var->isDisabled() ? ' disabled="disabled"' : '',
                        @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset));

        if ($var->type->hasHelper('rte') && $browser->hasFeature('rte')) {
            require_once 'Horde/Editor.php';
            if ($var->type->hasHelper('relativelinks')) {
                $editor = &Horde_Editor::singleton('xinha', array('id' => $varname, 'relativelinks' => true));
            } else {
                $editor = &Horde_Editor::singleton('xinha', array('id' => $varname));
            }
        }

        if ($var->type->hasHelper() && $browser->hasFeature('javascript')) {
            $html .= '<br /><table cellspacing="0"><tr><td>';
            Horde::addScriptFile('open_html_helper.js', 'horde');
            $imgId = $this->_genID($var->getVarName(), false) . 'ehelper';
            if ($var->type->hasHelper('emoticons')) {
                $html .= Horde::link('#', _("Emoticons"), '', '', 'openHtmlHelper(\'emoticons\', \'' . $var->getVarName() . '\'); return false;') . Horde::img('smile.png', _("Emoticons"), 'id="' . $imgId . '"', $GLOBALS['registry']->getImageDir('horde') . '/emoticons') . '</a>';
            }
            $html .= '</td></tr><tr><td><div ' . $this->_genID('htmlhelper_' . $var->getVarName()) . ' class="control"></div></td></tr></table>' . "\n";
        }

        return $html;
    }

    function _renderVarInput_countedtext($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<textarea name="%s" id="%s" cols="%s" rows="%s"%s%s>%s</textarea>',
                       $varname,
                       $varname,
                       (int)$var->type->getCols(),
                       (int)$var->type->getRows(),
                       $this->_getActionScripts($form, $var),
                       $var->isDisabled() ? ' disabled="disabled"' : '',
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset));
    }

    function _renderVarInput_address($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<textarea name="%s" id="%s" cols="%s" rows="%s"%s%s>%s</textarea>',
                       $varname,
                       $varname,
                       (int)$var->type->getCols(),
                       (int)$var->type->getRows(),
                       $this->_getActionScripts($form, $var),
                       $var->isDisabled() ? ' disabled="disabled"' : '',
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset));
    }

    function _renderVarInput_addresslink($form, &$var, &$vars)
    {
        return '';
    }

    function _renderVarInput_pgp($form, &$var, &$vars)
    {
        return $this->_renderVarInput_longtext($form, $var, $vars);
    }

    function _renderVarInput_smime($form, &$var, &$vars)
    {
        return $this->_renderVarInput_longtext($form, $var, $vars);
    }

    function _renderVarInput_country($form, &$var, &$vars)
    {
        return $this->_renderVarInput_enum($form, $var, $vars);
    }

    function _renderVarInput_date($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_time($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" size="5" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_hourminutesecond($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $time = $var->type->getTimeParts($var->getValue($vars));

        /* Output hours. */
        $hours = array('' => _("hh"));
        for ($i = 0; $i <= 23; $i++) {
            $hours[$i] = $i;
        }
        $html = sprintf('<select name="%s[hour]" id="%s[hour]"%s>%s</select>',
                        $varname,
                        $varname,
                        $this->_getActionScripts($form, $var),
                        $this->_selectOptions($hours, ($time['hour'] === '') ? '' : $time['hour']));

        /* Output minutes. */
        $minutes = array('' => _("mm"));
        for ($i = 0; $i <= 59; $i++) {
            $m = sprintf('%02d', $i);
            $minutes[$m] = $m;
        }
        $html .= sprintf('<select name="%s[minute]" id="%s[minute]"%s>%s</select>',
                         $varname,
                         $varname,
                         $this->_getActionScripts($form, $var),
                         $this->_selectOptions($minutes, ($time['minute'] === '') ? '' : sprintf('%02d', $time['minute'])));

        /* Return if seconds are not required. */
        if (!$var->type->getProperty('show_seconds')) {
            return $html;
        }

        /* Output seconds. */
        $seconds = array('' => _("ss"));
        for ($i = 0; $i <= 59; $i++) {
            $s = sprintf('%02d', $i);
            $seconds[$s] = $s;
        }
        return $html . sprintf('<select name="%s[second]" id="%s[second]"%s>%s</select>',
                               $varname,
                               $varname,
                               $this->_getActionScripts($form, $var),
                               $this->_selectOptions($seconds, ($time['second'] === '') ? '' : sprintf('%02d', $time['second'])));
    }

    function _renderVarInput_monthyear($form, &$var, &$vars)
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
        if ($var->type->getProperty('start_year') > $var->type->getProperty('end_year')) {
            for ($i = $var->type->getProperty('start_year'); $i >= $var->type->getProperty('end_year'); $i--) {
                $dates['year'][$i] = $i;
            }
        } else {
            for ($i = $var->type->getProperty('start_year'); $i <= $var->type->getProperty('end_year'); $i++) {
                $dates['year'][$i] = $i;
            }
        }
        return sprintf('<select name="%s" id="%s"%s>%s</select>',
                       $var->type->getMonthVar($var),
                       $var->type->getMonthVar($var),
                       $this->_getActionScripts($form, $var),
                       $this->_selectOptions($dates['month'], $vars->get($var->type->getMonthVar($var)))) .
            sprintf('<select name="%s" id="%s"%s>%s</select>',
                    $var->type->getYearVar($var),
                    $var->type->getYearVar($var),
                    $this->_getActionScripts($form, $var),
                    $this->_selectOptions($dates['year'], $vars->get($var->type->getYearVar($var))));
    }

    function _renderVarInput_monthdayyear($form, &$var, &$vars)
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
        if ($var->type->getProperty('start_year') > $var->type->getProperty('end_year')) {
            for ($i = $var->type->getProperty('start_year'); $i >= $var->type->getProperty('end_year'); $i--) {
                $dates['year'][$i] = $i;
            }
        } else {
            for ($i = $var->type->getProperty('start_year'); $i <= $var->type->getProperty('end_year'); $i++) {
                $dates['year'][$i] = $i;
            }
        }
        $date = $var->type->getDateParts($var->getValue($vars));

        // TODO: use NLS to get the order right for the Rest Of The
        // World.
        $html = '';
        $date_parts = array('month', 'day', 'year');
        foreach ($date_parts as $part) {
            $varname = @htmlspecialchars($var->getVarName() . '[' . $part . ']', ENT_QUOTES, $this->_charset);
            $html .= sprintf('<select name="%s" id="%s"%s>%s</select>',
                             $varname,
                             $varname,
                             $this->_getActionScripts($form, $var),
                             $this->_selectOptions($dates[$part], $date[$part]));
        }

        if ($var->type->getProperty('picker') && $GLOBALS['browser']->hasFeature('javascript')) {
            Horde::addScriptFile('open_calendar.js', 'horde');
            $imgId = $this->_genID($var->getVarName(), false) . 'goto';
            $html .= '<div id="goto" style="display:none"></div>' .
                Horde::link('#', _("Select a date"), '', '', 'openCalendar(\'' . $imgId . '\', \'' . $var->getVarName() . '\'); return false;') . Horde::img('calendar.png', _("Calendar"), 'id="' . $imgId . '"', $GLOBALS['registry']->getImageDir('horde')) . "</a>\n";
        }

        return $html;
    }

    /**
     * @since Horde 3.2
     */
    function _renderVarInput_datetime(&$form, &$var, &$vars)
    {
        return $this->_renderVarInput_monthdayyear($form, $var, $vars) .
            $this->_renderVarInput_hourminutesecond($form, $var, $vars);
    }

    /**
     * @since Horde 3.2
     */
    function _renderVarInput_sound(&$form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $value = @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset);
        $html = '<ul class="sound-list">';
        if (!$var->isRequired()) {
            $html .= '<li><label><input type="radio" id="' . $varname . '" name="' . $varname . '" value=""' . (!$value ? ' checked="checked"' : '') . ' /> ' . _("No Sound") . '</label></li>';
        }
        foreach ($var->type->getSounds() as $sound) {
            $sound = @htmlspecialchars($sound, ENT_QUOTES, $this->_charset);
            $html .= '<li><label><input type="radio" id="' . $varname . '" name="' . $varname . '" value="' . $sound . '"' . ($value == $sound ? ' checked="checked"' : '') . ' />' . $sound . '</label>'
                . ' <embed autostart="false" src="'. $GLOBALS['registry']->get('themesuri', 'horde') . '/sounds/' . $sound . '" /></li>';
        }
        return $html . '</ul>';
    }

    function _renderVarInput_colorpicker($form, &$var, &$vars)
    {
        global $registry, $browser;

        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $color = $var->getValue($vars);
        if ($color) {
            require_once 'Horde/Image.php';
            $style = ' style="background-color:' . $color . ';color:'
                . (Horde_Image::brightness($color) < 128 ? '#fff' : '#000') . '"';
        } else {
            $style = '';
        }
        $html = '<table cellspacing="0"><tr><td>'
            . '<input type="text" size="10" maxlength="7" name="'
            . $varname . '" id="' . $varname . '"' . $style
            . ' value="' . @htmlspecialchars($color, ENT_QUOTES, $this->_charset)
            . '" /></td>';
        if ($browser->hasFeature('javascript')) {
            Horde::addScriptFile('prototype.js', 'horde', true);
            Horde::addScriptFile('colorpicker.js', 'horde', true);
            $html .= '<td>'
                . Horde::link('#', _("Color Picker"), '', '',
                              'new ColorPicker({ color: \'' . htmlspecialchars($color) . '\', offsetParent: Event.element(event), update: [[\'' . $varname . '\', \'value\'], [\'' . $varname . '\', \'background\']] }); return false;')
                . Horde::img('colorpicker.png', _("Color Picker"), 'height="16"', $registry->getImageDir('horde')) . '</a></td>';
        }
        return $html . '</tr></table>';
    }

    function _renderVarInput_sorter($form, &$var, &$vars)
    {
        global $registry;

        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $instance = $var->type->getProperty('instance');

        Horde::addScriptFile('sorter.js', 'horde', true);

        return '<input type="hidden" name="' . $varname .
            '[array]" value="" ' . $this->_genID($varname . '[array]') . '/>' .
            '<select class="leftFloat" multiple="multiple" size="' .
            (int)$var->type->getSize() . '" name="' . $varname .
            '[list]" onchange="' . $instance . '.deselectHeader();" ' .
            $this->_genID($varname . '[list]') . '>' .
            $var->type->getOptions($var->getValue($vars)) . '</select><div class="leftFloat">' .
            Horde::link('#', _("Move up"), '', '', $instance . '.moveColumnUp(); return false;') . Horde::img('nav/up.png', _("Move up"), '', $registry->getImageDir('horde')) . '</a><br />' .
            Horde::link('#', _("Move up"), '', '', $instance . '.moveColumnDown(); return false;') . Horde::img('nav/down.png', _("Move down"), '', $registry->getImageDir('horde')) . '</a></div>' .
            '<script type="text/javascript">' . "\n" .
            sprintf('%1$s = new Horde_Form_Sorter(\'%1$s\', \'%2$s\', \'%3$s\');' . "\n",
                    $instance, $varname, $var->type->getHeader()) .
            sprintf("%s.setHidden();\n</script>\n", $instance);
    }

    function _renderVarInput_assign($form, &$var, &$vars)
    {
        global $registry;

        Horde::addScriptFile('form_assign.js', 'horde', true);

        $name = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $size = $var->type->getSize();
        $width = $var->type->getWidth();
        $lhdr = (bool)$var->type->getHeader(0);
        $rhdr = (bool)$var->type->getHeader(1);
        $this->_addOnLoadJavascript('Horde_Form_Assign.setField(\'' . $form->getName() . '\', \'' . $var->getVarName() . '\');');

        return '<input type="hidden" name="' . $name . '__values" />' .
            '<table style="width:auto"><tr><td>' .
            sprintf('<select name="%s__left" multiple="multiple" size="%d" style="width:%s"%s>',
                    $name, $size, $width,
                    $lhdr ? ' onchange="Horde_Form_Assign.deselectHeaders(\'' . $form->getName() . '\', \'' . $var->getVarName() . '\', 0);"' : '') .
            $var->type->getOptions(0, $form->getName(), $var->getVarName()) .
            '</select></td><td>' .
            '<a href="#" onclick="Horde_Form_Assign.move(\'' . $form->getName() . '\', \'' . $var->getVarName() . '\', 0); return false;">' .
            Horde::img('rhand.png', _("Add"), null, $registry->getImageDir('horde')) .
            '</a><br /><a href="#" onclick="Horde_Form_Assign.move(\'' .
            $form->getName() . '\', \'' . $var->getVarName() . '\', 1); return false;">' .
            Horde::img('lhand.png', _("Remove"), null, $registry->getImageDir('horde')) .
            '</a></td><td>' .
            sprintf('<select name="%s__right" multiple="multiple" size="%d" style="width:%s"%s>',
                    $name, $size, $width,
                    $rhdr ? ' onchange="Horde_Form_Assign.deselectHeaders(\'' . $form->getName() . '\', \'' . $var->getVarName() . '\', 1);"' : '') .
            $var->type->getOptions(1, $form->getName(), $var->getVarName()) .
            '</select></td></tr></table>';
    }

    function _renderVarInput_invalid($form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_invalid($form, $var, $vars);
    }

    function _renderVarInput_enum($form, &$var, &$vars)
    {
        $values = $var->getValues();
        $prompt = $var->type->getPrompt();
        $htmlchars = $var->getOption('htmlchars');
        if (!empty($prompt)) {
            $prompt = '<option value="">' . ($htmlchars ? $prompt : @htmlspecialchars($prompt, ENT_QUOTES, $this->_charset)) . '</option>';
        }
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<select name="%s" id="%s" %s>%s%s</select>',
                       $varname,
                       $varname,
                       $this->_getActionScripts($form, $var),
                       $prompt,
                       $this->_selectOptions($values, $var->getValue($vars), $htmlchars));
    }

    function _renderVarInput_mlenum($form, &$var, &$vars)
    {
        $varname = $var->getVarName();
        $hvarname = @htmlspecialchars($varname, ENT_QUOTES, $this->_charset);
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
                        $hvarname,
                        @htmlspecialchars($selected['1'], ENT_QUOTES, $this->_charset),
                        $this->_genID($varname . '[old]'));

        /* First level. */
        require_once 'Horde/Array.php';
        $values_1 = Horde_Array::valuesToKeys(array_keys($values));
        $html .= sprintf('<select %s name="%s[1]" onchange="%s"%s>',
                         $this->_genID($varname . '[1]'),
                         $hvarname,
                         'if (this.value) { document.' . $form->getName() . '.formname.value=\'\';' . 'document.' . $form->getName() . '.submit() }',
                         ($var->hasAction() ? ' ' . $this->_genActionScript($form, $var->_action, $varname) : ''));
        if (!empty($prompts)) {
            $html .= '<option value="">' . @htmlspecialchars($prompts[0], ENT_QUOTES, $this->_charset) . '</option>';
        }
        $html .= $this->_selectOptions($values_1, $selected['1']);
        $html .= '</select>';

        /* Second level. */
        $html .= sprintf('<select %s name="%s[2]"%s>',
                         $this->_genID($varname . '[2]'),
                         $hvarname,
                         ($var->hasAction() ? ' ' . $this->_genActionScript($form, $var->_action, $varname) : ''));
        if (!empty($prompts)) {
            $html .= '<option value="">' . @htmlspecialchars($prompts[1], ENT_QUOTES, $this->_charset) . '</option>';
        }
        $values_2 = array();
        if (!empty($selected['1'])) {
            $values_2 = &$values[$selected['1']];
        }
        return $html . $this->_selectOptions($values_2, $selected['2']) . '</select>';
    }

    function _renderVarInput_multienum($form, &$var, &$vars)
    {
        $values = $var->getValues();
        $selected = $vars->getExists($var->getVarName(), $wasset);
        if (!$wasset) {
            $selected = $var->getDefault();
        }
        return sprintf('<select multiple="multiple" size="%s" name="%s[]" %s>%s</select>',
                       (int)$var->type->size,
                       @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var),
                       $this->_multiSelectOptions($values, $selected)) .
            "<br />\n" . _("To select multiple items, hold down the Control (PC) or Command (Mac) key while clicking.") . "\n";
    }

    function _renderVarInput_keyval_multienum($form, &$var, &$vars)
    {
        return $this->_renderVarInput_multienum($form, $var, $vars);
    }

    function _renderVarInput_radio($form, &$var, &$vars)
    {
        return $this->_radioButtons($var->getVarName(),
                                    $var->getValues(),
                                    $var->getValue($vars),
                                    $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_set($form, &$var, &$vars)
    {
        $html = $this->_checkBoxes($var->getVarName(),
                                   $var->getValues(),
                                   $var->getValue($vars),
                                   $this->_getActionScripts($form, $var));

        if ($var->type->getProperty('checkAll')) {
            $form_name = $form->getName();
            $var_name = $var->getVarName() . '[]';
            $function_name = 'select'  . $form_name . $var->getVarName();
            $enable = _("Select all");
            $disable = _("Select none");
            $invert = _("Invert selection");
            $html .= <<<EOT
<script type="text/javascript">
function $function_name()
{
    for (var i = 0; i < document.$form_name.elements.length; i++) {
        f = document.$form_name.elements[i];
        if (f.name != '$var_name') {
            continue;
        }
        if (arguments.length) {
            f.checked = arguments[0];
        } else {
            f.checked = !f.checked;
        }
    }
}
</script>
<a href="#" onclick="$function_name(true); return false;">$enable</a>,
<a href="#" onclick="$function_name(false); return false;">$disable</a>,
<a href="#" onclick="$function_name(); return false;">$invert</a>
EOT;
        }

        return $html;
    }

    function _renderVarInput_link($form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_link($form, $var, $vars);
    }

    function _renderVarInput_html($form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_html($form, $var, $vars);
    }

    function _renderVarInput_email($form, &$var, &$vars)
    {
        return sprintf('<input type="text" name="%s" id="%s" value="%s"%s />',
                       $var->getVarName(),
                       $var->getVarName(),
                       @htmlspecialchars($var->getValue($vars)),
                       $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_matrix($form, &$var, &$vars)
    {
        $varname   = $var->getVarName();
        $var_array = $var->getValue($vars);
        $cols      = $var->type->getCols();
        $rows      = $var->type->getRows();
        $matrix    = $var->type->getMatrix();
        $new_input = $var->type->getNewInput();

        $html = '<table cellspacing="0"><tr>';

        $html .= '<td class="rightAlign" width="20%"></td>';
        foreach ($cols as $col_title) {
            $html .= '<td align="center" width="1%">' . htmlspecialchars($col_title) . '</td>';
        }
        $html .= '<td class="rightAlign" width="60%"></td></tr>';

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
                $html .= sprintf('<td align="center"><input type="checkbox" class="checkbox" name="%s[n][v][%s]" /></td>', $varname, $col_id);
            }
            $html .= '<td> </td></tr>';
        }

        /* Loop through the rows and create checkboxes for each column. */
        foreach ($rows as $row_id => $row_title) {
            $html .= sprintf('<tr><td>%s</td>', $row_title);
            foreach ($cols as $col_id => $col_title) {
                $html .= sprintf('<td align="center"><input type="checkbox" class="checkbox" name="%s[r][%s][%s]"%s /></td>', $varname, $row_id, $col_id, (!empty($matrix[$row_id][$col_id]) ? ' checked="checked"' : ''));
            }
            $html .= '<td> </td></tr>';
        }

        return $html . '</table>';
    }

    function _renderVarInput_password($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="password" name="%s" id="%s" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_emailconfirm($form, &$var, &$vars)
    {
        $email = $var->getValue($vars);
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s[original]" id="%s[original]" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($email['original'], ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var)) .
            ' ' . sprintf('<input type="text" name="%s[confirm]" id="%s[confirm]" value="%s"%s />',
                          $varname,
                          $varname,
                          @htmlspecialchars($email['confirm'], ENT_QUOTES, $this->_charset),
                          $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_passwordconfirm($form, &$var, &$vars)
    {
        $password = $var->getValue($vars);
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="password" name="%s[original]" id="%s[original]" value="%s"%s />',
                       $varname,
                       $varname,
                       @htmlspecialchars($password['original'], ENT_QUOTES, $this->_charset),
                       $this->_getActionScripts($form, $var)) .
            ' ' . sprintf('<input type="password" name="%s[confirm]" id="%s[confirm]" value="%s"%s />',
                          $varname,
                          $varname,
                          @htmlspecialchars($password['confirm'], ENT_QUOTES, $this->_charset),
                          $this->_getActionScripts($form, $var));
    }

    function _renderVarInput_boolean($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $html = '<input type="checkbox" class="checkbox" name="' .  $varname . '"' .
            ' id="' . $varname . '"' . ($var->getValue($vars) ? ' checked="checked"' : '');
        if ($var->hasAction()) {
            $html .= $this->_genActionScript($form, $var->_action,
                                             $var->getVarName());
        }
        return $html . ' />';
    }

    function _renderVarInput_creditcard($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $html = '<input type="text" name="' . $varname . '" id="' . $varname . '" value="' .
            @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset) . '"';
        if ($var->hasAction()) {
            $html .= $this->_genActionScript($form, $var->_action,
                                             $var->getVarName());
        }
        return $html . ' />';
    }

    function _renderVarInput_obrowser($form, &$var, &$vars)
    {
        $varname = $var->getVarName();
        $varvalue = $vars->get($varname);
        $fieldId = $this->_genID(md5(uniqid(rand(), true)), false) . 'id';
        $html = '
            <script type="text/javascript">
            var obrowserWindowName;
            function obrowserCallback(name, oid)
            {
                if (name == obrowserWindowName) {
                    document.getElementById(\'' . $fieldId . '\').value = oid;
                    return false;
                } else {
                    return "Invalid window name supplied";
                }
            }
            </script>
            ';
        $html .= sprintf('<input type="hidden" name="%s" id="%s"%s value="%s">',
                         @htmlspecialchars($varname, ENT_QUOTES, $this->_charset),
                         $fieldId,
                         $this->_getActionScripts($form, $var),
                         @htmlspecialchars($varvalue, ENT_QUOTES, $this->_charset));
        if (!empty($varvalue)) {
            $html .= $varvalue;
        }

        if ($GLOBALS['browser']->hasFeature('javascript')) {
            Horde::addScriptFile('popup.js', 'horde', true);
            $html .= Horde::link($GLOBALS['registry']->get('webroot', 'horde') . '/services/obrowser/', _("Select an object"), '', '_blank', 'obrowserWindow = popup(this.href); obrowserWindowName = obrowserWindow.name; return false;') . Horde::img('tree/leaf.png', _("Object"), '', $GLOBALS['registry']->getImageDir('horde')) . "</a>\n";
        }

        return $html;
    }

    function _renderVarInput_dblookup($form, &$var, &$vars)
    {
        return $this->_renderVarInput_enum($form, $var, $vars);
    }

    function _renderVarInput_figlet($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s" id="%s" size="%s" value="%s" />',
                       $varname,
                       $varname,
                       strlen($var->type->getText()),
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset)) .
            '<br />' . _("Enter the letters below:") . '<br />' .
            $this->_renderVarDisplay_figlet($form, $var, $vars);
    }

    function _renderVarInput_captcha($form, &$var, &$vars)
    {
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        return sprintf('<input type="text" name="%s" id="%s" size="%s" value="%s" />',
                       $varname,
                       $varname,
                       strlen($var->type->getText()),
                       @htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset)) .
            '<br />' . _("Enter the letters below:") . '<br />' .
            $this->_renderVarDisplay_captcha($form, $var, $vars);
    }

    function _renderVarDisplayDefault($form, &$var, &$vars)
    {
        return nl2br(@htmlspecialchars($var->getValue($vars), ENT_QUOTES, $this->_charset));
    }

    function _renderVarDisplay_html($form, &$var, &$vars)
    {
        // Since this is an HTML type we explicitly don't escape
        // it. User beware.
        return $var->getValue($vars);
    }

    function _renderVarDisplay_email($form, &$var, &$vars)
    {
        $email_val = $var->getValue($vars);

        if ($var->type->getProperty('link_compose')) {
            // Multiple email addresses?
            if ($var->type->getProperty('allow_multi')) {
                require_once 'Horde/MIME.php';
                $addrs = MIME::rfc822Explode($email_val);
            } else {
                $addrs = array($email_val);
            }

            $link = '';
            foreach ($addrs as $addr) {
                $addr = trim($addr);

                $display_email = $addr;
                if ($var->type->getProperty('strip_domain') && strpos($addr, '@') !== false) {
                    $display_email = str_replace(array('@', '.'),
                                                 array(' (at) ', ' (dot) '),
                                                 $addr);
                }

                // Format the address according to RFC822.
                $mailbox_host = explode('@', $addr);
                if (!isset($mailbox_host[1])) {
                    $mailbox_host[1] = '';
                }

                $name = $var->type->getProperty('link_name');

                require_once 'Horde/MIME.php';
                $address = MIME::rfc822WriteAddress($mailbox_host[0], $mailbox_host[1], $name);

                // Get rid of the trailing @ (when no host is included in
                // the email address).
                $address = str_replace('@>', '>', $address);
                $mail_link = $GLOBALS['registry']->call('mail/compose', array(array('to' => addslashes($address))));
                if (is_a($mail_link, 'PEAR_Error')) {
                    $mail_link = 'mailto:' . urlencode($address);
                }

                if (!empty($link)) {
                    $link .= ', ';
                }
                $link .= Horde::link($mail_link, $addr) . @htmlspecialchars($display_email, ENT_QUOTES, $this->_charset) . '</a>';
            }

            return $link;
        } else {
            $email_val = trim($email_val);

            if ($var->type->getProperty('strip_domain') && strpos($email_val, '@') !== false) {
                $email_val = str_replace(array('@', '.'),
                                         array(' (at) ', ' (dot) '),
                                         $email_val);
            }

            return nl2br(@htmlspecialchars($email_val, ENT_QUOTES, $this->_charset));
        }
    }

    function _renderVarDisplay_password($form, &$var, &$vars)
    {
        return '********';
    }

    function _renderVarDisplay_passwordconfirm($form, &$var, &$vars)
    {
        return '********';
    }

    function _renderVarDisplay_octal($form, &$var, &$vars)
    {
        return sprintf('0%o', octdec($var->getValue($vars)));
    }

    function _renderVarDisplay_boolean($form, &$var, &$vars)
    {
        return $var->getValue($vars) ? _("Yes") : _("No");
    }

    function _renderVarDisplay_enum($form, &$var, &$vars)
    {
        $values = $var->getValues();
        $value = $var->getValue($vars);
        if (count($values) == 0) {
            return _("No values");
        } elseif (isset($values[$value]) && $value != '') {
            return @htmlspecialchars($values[$value], ENT_QUOTES, $this->_charset);
        }
    }

    function _renderVarDisplay_radio($form, &$var, &$vars)
    {
        $values = $var->getValues();
        if (count($values) == 0) {
            return _("No values");
        } elseif (isset($values[$var->getValue($vars)])) {
            return @htmlspecialchars($values[$var->getValue($vars)], ENT_QUOTES, $this->_charset);
        }
    }

    function _renderVarDisplay_multienum($form, &$var, &$vars)
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
            return @htmlspecialchars(implode(', ', $display), ENT_QUOTES, $this->_charset);
        }
    }

    function _renderVarDisplay_set($form, &$var, &$vars)
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
            return @htmlspecialchars(implode(', ', $display), ENT_QUOTES, $this->_charset);
        }
    }

    function _renderVarDisplay_image($form, &$var, &$vars)
    {
        $image = $var->getValue($vars);

        /* Check if existing image data is being loaded. */
        $var->type->loadImageData($image);

        if (empty($image['img'])) {
            return '';
        }

        $img = Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/images/view.php');
        if (isset($image['img']['vfs_id'])) {
            /* Calling an image from VFS. */
            $img = Util::addParameter($img, array('f' => $image['img']['vfs_id'],
                                                  's' => 'vfs',
                                                  'p' => $image['img']['vfs_path']));
        } else {
            /* Calling an image from a tmp directory (uploads). */
            $img = Util::addParameter($img, 'f', $image['img']['file']);
        }

        return Horde::img($img, '', '', '');
    }

    function _renderVarDisplay_phone($form, &$var, &$vars)
    {
        global $registry;

        $number = $var->getValue($vars);
        $html = @htmlspecialchars($number, ENT_QUOTES, $this->_charset);

        if ($number && $registry->hasMethod('telephony/dial')) {
            $url = $registry->call('telephony/dial', array($number));
            $label = sprintf(_("Dial %s"), $number);
            $html .= ' ' . Horde::link($url, $label) . Horde::img('phone.png', $label, '', $registry->getImageDir('horde')) . '</a>';
        }

        return $html;
    }

    function _renderVarDisplay_cellphone($form, &$var, &$vars)
    {
        global $registry;

        $html = $this->_renderVarDisplay_phone($form, $var, $vars);

        $number = $var->getValue($vars);
        if ($number && $registry->hasMethod('sms/compose')) {
            $url = $registry->link('sms/compose', array('to' => $number));
            $html .= ' ' . Horde::link($url, _("Send SMS")) . Horde::img('mobile.png', _("Send SMS"), '', $registry->getImageDir('horde')) . '</a>';
        }

        return $html;
    }

    function _renderVarDisplay_address($form, &$var, &$vars, $text = true)
    {
        global $registry;

        $address = $var->getValue($vars);
        if (empty($address)) {
            return '';
        }

        $info = $var->type->parse($address);

        $google_icon = 'map.png';
        if (!empty($info['country'])) {
            switch ($info['country']) {
            case 'uk':
                /* Multimap.co.uk generated map */
                $mapurl = 'http://www.multimap.com/map/browse.cgi?pc='
                    . urlencode($info['zip']);
                $desc = _("Multimap UK map");
                $icon = 'map.png';
                break;

            case 'au':
                /* Whereis.com.au generated map */
                $mapurl = 'http://www.whereis.com.au/whereis/mapping/geocodeAddress.do?';
                $desc = _("Whereis Australia map");
                $icon = 'map.png';
                /* See if it's the street number & name. */
                if (isset($info['streetNumber']) &&
                    isset($info['streetName'])) {
                    $mapurl .= '&streetNumber='
                        . urlencode($info['streetNumber']) . '&streetName='
                        . urlencode($info['streetName']);
                }
                /* Look for "Suburb, State". */
                if (isset($info['city'])) {
                    $mapurl .= '&suburb=' . urlencode($info['city']);
                }
                /* Look for "State <4 digit postcode>". */
                if (isset($info['state'])) {
                    $mapurl .= '&state=' . urlencode($info['state']);
                }
                break;

            case 'us':
            case 'ca':
                /* American/Canadian address style. */
                /* Mapquest generated map */
                $mapurl = 'http://www.mapquest.com/maps/map.adp?size=big&zoom=7';
                $desc = _("MapQuest map");
                $icon = 'map.png';
                if (!empty($info['street'])) {
                    $mapurl .= '&address=' . urlencode($info['street']);
                }
                if (!empty($info['city'])) {
                    $mapurl .= '&city=' . urlencode($info['city']);
                }
                if (!empty($info['state'])) {
                    $mapurl .= '&state=' . urlencode($info['state']);
                }
                if (!empty($info['zip'])) {
                    if ($info['country'] == 'ca') {
                        $mapurl .= '&country=CA';
                    }
                    $mapurl .= '&zipcode=' . urlencode($info['zip']);
                }

                /* Yahoo! generated map. */
                $mapurl2 = 'http://us.rd.yahoo.com/maps/home/submit_a/*-http://maps.yahoo.com/maps?srchtype=a&getmap=Get+Map&';
                $desc2 = _("Yahoo! map");
                $icon2 = 'map.png';
                if (!empty($info['street'])) {
                    $mapurl2 .= '&addr=' . urlencode($info['street']);
                }
                /* Give precedence to zipcode over city/state */
                if (empty($info['zip']) &&
                    !empty($info['city']) && !empty($info['state'])) {
                    $mapurl2 .= '&csz='
                        . urlencode($info['city'] . ' ' . $info['state']);
                }
                if (!empty($info['zip'])) {
                    if (preg_match('|([a-zA-Z]\d[a-zA-Z])\s?(\d[a-zA-Z]\d)|', $info['zip'], $pcParts)) {
                        $mapurl2 .= '&country=ca';
                        /* make sure the postal-code has a space */
                        $info['zip'] = $pcParts[1] . ' ' . $pcParts[2];
                    }
                    $mapurl2 .= '&csz=' . urlencode($info['zip']);
                }
                break;

            default:
                if (!count($info)) {
                    break;
                }
                /* European address style. */
                $google_icon = 'map_eu.png';
                /* Mapquest generated map. */
                $mapurl2 = 'http://www.mapquest.com/maps/map.adp?country=' . String::upper($info['country']);
                $desc2 = _("MapQuest map");
                $icon2 = 'map_eu.png';
                if (!empty($info['street'])) {
                    $mapurl2 .= '&address=' . urlencode($info['street']);
                }
                if (!empty($info['zip'])) {
                    $mapurl2 .= '&zipcode=' . urlencode($info['zip']);
                }
                if (!empty($info['city'])) {
                    $mapurl2 .= '&city=' . urlencode($info['city']);
                }
                break;
            }
        }

        $html = $text ? nl2br(@htmlspecialchars($address, ENT_QUOTES, $this->_charset)) : '';
        if (!empty($mapurl)) {
            $html .= '&nbsp;&nbsp;' . Horde::link(Horde::externalUrl($mapurl), $desc, null, '_blank') . Horde::img($icon, $desc, '', $registry->getImageDir('horde')) . '</a>';
        }
        if (!empty($mapurl2)) {
            $html .= '&nbsp;' . Horde::link(Horde::externalUrl($mapurl2), $desc2, null, '_blank') . Horde::img($icon2, $desc2, '', $registry->getImageDir('horde')) . '</a>';
        }

        /* Google generated map. */
        if ($address) {
            $html .= '&nbsp;' . Horde::link(Horde::externalUrl('http://maps.google.com/maps?q=' . urlencode(preg_replace('/\r?\n/', ',', $address)) . '&hl=en'), _("Google Maps"), null, '_blank') . Horde::img($google_icon, _("Google Maps"), '', $registry->getImageDir('horde')) . '</a>';
        }

        return $html;
    }

    function _renderVarDisplay_addresslink($form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_address($form, $var, $vars, false);
    }

    function _renderVarDisplay_pgp($form, &$var, &$vars)
    {
        $key = $var->getValue($vars);
        if (empty($key)) {
            return '';
        }
        require_once 'Horde/Crypt.php';
        require_once 'Horde/Text/Filter.php';
        $pgp = Horde_Crypt::factory('pgp', $var->type->getPGPParams());
        return '<pre>' . $pgp->pgpPrettyKey($key) . '</pre>';
    }

    function _renderVarDisplay_smime($form, &$var, &$vars)
    {
        $cert = $var->getValue($vars);
        if (empty($cert)) {
            return '';
        }
        require_once 'Horde/Crypt.php';
        $smime = Horde_Crypt::factory('smime', $var->type->getSMIMEParams());
        return $smime->certToHTML($cert);
    }

    function _renderVarDisplay_country($form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_enum($form, $var, $vars);
    }

    function _renderVarDisplay_date($form, &$var, &$vars)
    {
        return htmlspecialchars($var->type->getFormattedTime($var->getValue($vars)));
    }

    function _renderVarDisplay_hourminutesecond($form, &$var, &$vars)
    {
        $time = $var->type->getTimeParts($var->getValue($vars));
        if (!$var->type->getProperty('show_seconds')) {
            return (int)$time['hour'] . ':' . sprintf('%02d', (int)$time['minute']);
        } else {
            return (int)$time['hour'] . ':' . sprintf('%02d', (int)$time['minute']) . ':' . sprintf('%02d', (int)$time['second']);
        }
    }

    function _renderVarDisplay_monthyear($form, &$var, &$vars)
    {
        return (int)$vars->get($var->getVarName() . '[month]') . ', ' . (int)$vars->get($var->getVarName() . '[year]');
    }

    function _renderVarDisplay_monthdayyear($form, &$var, &$vars)
    {
        $date = $var->getValue($vars);
        if ((is_array($date) && !empty($date['year']) &&
             !empty($date['month']) && !empty($date['day'])) ||
            (!is_array($date) && !empty($date) && $date != '0000-00-00')) {
            return $var->type->formatDate($date);
        }
        return '';
    }

    /**
     * @since Horde 3.2
     */
    function _renderVarDisplay_datetime($form, &$var, &$vars)
    {
        return htmlspecialchars($var->type->formatDate($var->getValue($vars))) . Horde_Form_Type_date::getAgo($var->getValue($vars));
    }

    function _renderVarDisplay_invalid($form, &$var, &$vars)
    {
        return '<span class="form-error">' . @htmlspecialchars($var->type->message, ENT_QUOTES, $this->_charset) . '</span>';
    }

    function _renderVarDisplay_link($form, &$var, &$vars)
    {
        $values = $var->type->values;
        if (!isset($values[0])) {
            $values = array($values);
        }

        $count = count($values);
        $html = '';
        for ($i = 0; $i < $count; $i++) {
            if (empty($values[$i]['url']) || empty($values[$i]['text'])) {
                continue;
            }
            if (!isset($values[$i]['target'])) {
                $values[$i]['target'] = '';
            }
            if (!isset($values[$i]['onclick'])) {
                $values[$i]['onclick'] = '';
            }
            if (!isset($values[$i]['title'])) {
                $values[$i]['title'] = '';
            }
            if (!isset($values[$i]['accesskey'])) {
                $values[$i]['accesskey'] = '';
            }
            if ($i > 0) {
                $html .= ' | ';
            }
            $html .= Horde::link($values[$i]['url'], $values[$i]['text'], 'widget', $values[$i]['target'], $values[$i]['onclick'], $values[$i]['title'], $values[$i]['accesskey']) . @htmlspecialchars($values[$i]['text'], ENT_QUOTES, $this->_charset) . '</a>';
        }

        return $html;
    }

    function _renderVarDisplay_dblookup($form, &$var, &$vars)
    {
        return $this->_renderVarDisplay_enum($form, $var, $vars);
    }

    function _renderVarDisplay_figlet($form, &$var, &$vars)
    {
        static $figlet;

        if (!isset($figlet)) {
            require_once 'Text/Figlet.php';
            $figlet = new Text_Figlet();
        }

        $result = $figlet->loadFont($var->type->getFont());
        if (is_a($result, 'PEAR_Error')) {
            return $result->getMessage();
        }

        return '<pre>' . $figlet->lineEcho($var->type->getText()) . '</pre>';
    }

    function _renderVarDisplay_captcha($form, &$var, &$vars)
    {
        static $captcha;

        if (!isset($captcha)) {
            require_once 'Text/CAPTCHA.php';
            $captcha = Text_CAPTCHA::factory('Image');
        }

        $image = $captcha->init(150, 60, $var->type->getText(),
                                array('font_path' => dirname($var->type->getFont()) . '/',
                                      'font_file' => basename($var->type->getFont())));
        if (is_a($image, 'PEAR_Error')) {
            return $image->getMessage();
        }

        $cid = md5($var->type->getText());
        $cache = &Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'],
                                         Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
        $cache->set($cid, serialize(array('data' => $captcha->getCAPTCHAAsJPEG(),
                                          'ctype' => 'image/jpeg')));

        $url = Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/cacheview.php');
        $url = Util::addParameter($url, 'cid', $cid, false);

        return '<img src="' . $url . '" />';

    }

    function _renderVarInput_selectFiles($form, &$var, &$vars)
    {
        /* Needed for gollem js calls */
        $varname = @htmlspecialchars($var->getVarName(), ENT_QUOTES, $this->_charset);
        $html = sprintf('<input type="hidden" name="%s" id="%s" value="%s" />',
                        'selectlist_selectid',
                        'selectlist_selectid',
                        $var->type->getProperty('selectid')) .
            sprintf('<input type="hidden" name="%s" id="%s" />', 'actionID', 'actionID') .

            /* Form field. */
            sprintf('<input type="hidden" name="%s" id="%s" value="%s" />',
                    $varname,
                    $varname,
                    $var->type->getProperty('selectid'));

        /* Open window link. */
        $param = array($var->type->getProperty('link_text'),
                       $var->type->getProperty('link_style'),
                       $form->getName(),
                       $var->type->getProperty('icon'),
                       $var->type->getProperty('selectid'));
        $html .= $GLOBALS['registry']->call('files/selectlistLink', $param) . "<br />\n";

        if ($var->type->getProperty('selectid')) {
            $param = array($var->type->getProperty('selectid'));
            $files = $GLOBALS['registry']->call('files/selectlistResults', $param);
            if ($files) {
                $html .= '<ol>';
                foreach ($files as $id => $file) {
                    $dir = key($file);
                    $filename = current($file);
                    if ($GLOBALS['registry']->hasMethod('files/getViewLink')) {
                        $filename = basename($filename);
                        $url = $GLOBALS['registry']->call('files/getViewLink', array($dir, $filename));
                        $filename = Horde::link($url, _("Preview"), null, 'form_file_view') . @htmlspecialchars(Util::realPath($dir . '/' . $filename), ENT_QUOTES, $this->_charset) . '</a>';
                    } else {
                        if (!empty($dir) && ($dir != '.')) {
                            $filename = $dir . '/' . $filename;
                        }
                        $filename = @htmlspecialchars($filename, ENT_QUOTES, $this->_charset);
                    }
                    $html .= '<li>' . $filename . "</li>\n";
                }
                $html .= '</ol>';
            }
        }

        return $html;
    }

    function _renderVarInput_category($form, &$var, &$vars)
    {
        Horde::addScriptFile('horde.js', 'horde', true);
        require_once 'Horde/Prefs/CategoryManager.php';
        $this->_addOnLoadJavascript('addEvent(document.getElementById(\'' . $form->getName() . '\'), \'submit\', checkCategory);');
        return '<input type="hidden" name="new_category" />'
            . Prefs_CategoryManager::getJavaScript($form->getName(), $var->getVarName())
            . Prefs_CategoryManager::getSelect($var->getVarName(), $var->getValue($vars));
    }

    function _selectOptions(&$values, $selectedValue = false,
                            $htmlchars = false)
    {
        $result = '';
        $sel = false;
        foreach ($values as $value => $display) {
            if (!is_null($selectedValue) && !$sel &&
                $value == $selectedValue &&
                strlen($value) == strlen($selectedValue)) {
                $selected = ' selected="selected"';
                $sel = true;
            } else {
                $selected = '';
            }
            $result .= ' <option value="';
            $result .= $htmlchars
                ? $value
                : @htmlspecialchars($value, ENT_QUOTES, $this->_charset);
            $result .= '"' . $selected . '>';
            $result .= $htmlchars
                ? $display
                : @htmlspecialchars($display, ENT_QUOTES, $this->_charset);
            $result .= "</option>\n";
        }

        return $result;
    }

    function _multiSelectOptions(&$values, $selectedValues)
    {
        if (!is_array($selectedValues)) {
            $selectedValues = array();
        } else {
            $selectedValues = array_flip($selectedValues);
        }

        $result = '';
        $sel = false;
        foreach ($values as $value => $display) {
            if (isset($selectedValues[$value])) {
                $selected = ' selected="selected"';
            } else {
                $selected = '';
            }
            $result .= " <option value=\"" . @htmlspecialchars($value, ENT_QUOTES, $this->_charset) . "\"$selected>" . @htmlspecialchars($display, ENT_QUOTES, $this->_charset) . "</option>\n";
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
            $result .= sprintf('<input id="%s%s" type="checkbox" class="checkbox" name="%s[]" value="%s"%s%s /><label for="%s%s">&nbsp;%s</label><br />',
                               @htmlspecialchars($name, ENT_QUOTES, $this->_charset),
                               $i,
                               @htmlspecialchars($name, ENT_QUOTES, $this->_charset),
                               @htmlspecialchars($value, ENT_QUOTES, $this->_charset),
                               $checked,
                               $actions,
                               @htmlspecialchars($name, ENT_QUOTES, $this->_charset),
                               $i,
                               @htmlspecialchars($display, ENT_QUOTES, $this->_charset));
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
            $result .= sprintf('<input id="%s%s" type="radio" class="checkbox" name="%s" value="%s"%s%s /><label for="%s%s">&nbsp;%s</label><br />',
                               @htmlspecialchars($name, ENT_QUOTES, $this->_charset),
                               $i,
                               @htmlspecialchars($name, ENT_QUOTES, $this->_charset),
                               @htmlspecialchars($value, ENT_QUOTES, $this->_charset),
                               $checked,
                               $actions,
                               @htmlspecialchars($name, ENT_QUOTES, $this->_charset),
                               $i,
                               @htmlspecialchars($display, ENT_QUOTES, $this->_charset));
            $i++;
        }

        return $result;
    }

    function _genID($name, $fulltag = true)
    {
        $name = @htmlspecialchars($name, ENT_QUOTES, $this->_charset);
        return $fulltag ? 'id="' . $name . '"' : $name;
    }

    function _genActionScript($form, $action, $varname)
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

    function _getActionScripts($form, &$var)
    {
        $actions = '';
        if ($var->hasAction()) {
            $varname = $var->getVarName();
            $action = &$var->_action;
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
            return "<script type=\"text/javascript\">" .
                "<!--\n" .  implode("\n", $this->_onLoadJS) . "\n// -->\n" .
                "</script>";
        } else {
            return '';
        }
    }

}

<?php
/**
 * Horde_Mobile_Renderer:: output module for WML (Wireless Markup Language).
 *
 * $Horde: framework/Mobile/Mobile/Renderer/wml.php,v 1.32.10.13 2009-01-06 15:23:25 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Mobile
 */
class Horde_Mobile_Renderer_wml extends Horde_Mobile_Renderer {

    /**
     * Properly encode characters for output to a WML device.
     *
     * @param string $input  Characters to encode.
     *
     * @return string  The encoded text.
     */
    function escape($input)
    {
        // Encode entities.
        $output = @htmlspecialchars($input, ENT_COMPAT, NLS::getCharset());

        // Escape $ character in WML.
        $output = str_replace('$', '$$', $output);

        // Generate UTF-8.
        $output = String::convertCharset($output, NLS::getCharset(), 'utf-8');

        return $output;
    }

    /**
     * Creates the page in WML, allowing for different WML browser quirks.
     *
     * @param Horde_Mobile $deck  The deck to render.
     */
    function render(&$deck)
    {
        if ($deck->_debug) {
            header('Content-Type: text/plain; charset=utf-8');
        } else {
            header('Content-Type: text/vnd.wap.wml; charset=utf-8');
        }

        echo "<?xml version=\"1.0\"?>\n";
        if ($this->hasQuirk('ow_gui_1.3')) {
            echo '<!DOCTYPE wml PUBLIC "-//PHONE.COM//DTD WML 1.3//EN" "http://www.openwave.com/dtd/wml13.dtd">';
        } else {
            echo '<!DOCTYPE wml PUBLIC "-//WAPFORUM//DTD WML 1.1//EN" "http://www.wapforum.org/DTD/wml_1.1.xml">';
        }
        echo '<wml>';

        if (count($deck->_cards)) {
            foreach ($deck->_cards as $card) {
                $this->_renderCard($card);
            }
        } else {
            $title = $deck->get('title') ? ' title="' . $this->escape($deck->get('title')) . '"' : '';
            printf('<card%s>', $title);

            // Render all tags.
            foreach ($deck->_elements as $page_element) {
                $this->renderElement($page_element);
            }

            echo '</card>';
        }

        // End the WML page.
        echo '</wml>';
    }

    function _renderCard(&$card)
    {
        $name = $card->get('name') ? ' id="' . $this->escape($card->get('name')) . '"' : '';
        $title = $card->get('title') ? ' title="' . $this->escape($card->get('title')) . '"' : '';
        printf('<card%s%s>', $name, $title);

        // Initialize WML variables with their default values.
        if (!is_null($card->_form)) {
            echo '<onevent type="onenterforward"><refresh>';
            $defaults = $card->_form->getDefaults();
            foreach ($defaults as $d) {
                printf('<setvar name="_%s" value="%s"/>', $d['name'], $this->escape($d['value']));
            }
            echo '</refresh></onevent>';
        }

        if (count($card->_softkeys)) {
            if (count($card->_softkeys) == 1) {
                // If there is only one softkey, make it of type
                // 'options' so that it always shows up on the right,
                // instead of having to share the left softkey with
                // active links, making it much harder to get to.
                $type = 'options';
            } else {
                $type = 'accept';
            }
            foreach ($card->_softkeys as $key) {
                echo '<do type="' . $type . '" label="' . $this->escape($key['label']) . '"><go href="' . $key['url'] . '"/></do>';
            }
        }

        // Render all tags.
        foreach ($card->_elements as $page_element) {
            $this->renderElement($page_element);
        }

        echo '</card>';
    }

    function _renderLink(&$link)
    {
        $title_option = $link->get('title') ? sprintf(' title="%s"', $this->escape($link->get('title'))) : '';

        printf('<a%s href="%s">%s</a>',
               $title_option, str_replace('&amp;amp;', '&amp;', $this->escape($link->get('url'))),
               $this->escape($link->get('label')));
    }

    function _renderLinkset(&$linkset)
    {
        if (count($linkset->_elements)) {
            echo '<p>';
            if ($this->isBrowser('up')) {
                echo '<select>';
                foreach ($linkset->_elements as $val) {
                    $title = $val->get('title') ? ' title="' . $this->escape($val->get('title')) . '"' : '';
                    printf('<option onpick="%s"%s>%s</option>',
                           str_replace('&amp;amp;', '&amp;', $this->escape($val->get('url'))),
                           $title,
                           $this->escape($val->get('label')));
                }
                echo '</select>';
            } else {
                foreach ($linkset->_elements as $val) {
                    $this->_renderLink($val);
                    echo '<br />';
                }
            }
            echo '</p>';
        }
    }

    function _renderText(&$element)
    {
        foreach ($element->_attributes as $attribute) {
            echo '<' . $attribute . '>';
        }

        if ($element->get('linebreaks')) {
            echo nl2br($this->escape($element->get('text')));
        } else {
            echo $this->escape($element->get('text'));
        }

        $attributes = array_reverse($element->_attributes);
        foreach ($attributes as $attribute) {
            echo '</' . $attribute . '>';
        }
    }

    function _renderImage(&$image)
    {
        $attributes = '';
        foreach ($image->_attributes as $attribute => $value) {
            $attributes .= sprintf(' %s="%s"', $attribute, $value);
        }
        printf('<img src="%s.wbmp"%s/>', $image->_src, $attributes);
    }

    function _renderInput(&$input)
    {
        $type = ' type="' . $input->get('type') . '"';
        $size = $input->get('size') ? sprintf(' size="%d"', $input->get('size')) : '';
        $maxlength = $input->get('maxlength') ? sprintf(' maxlength="%d"', $input->get('maxlength')) : '';

        printf('%s<input emptyok="true" format="%s"%s name="_%s" value="%s"%s%s/>',
               $this->escape($input->get('label')), $input->get('format'),
               $type, $this->escape($input->get('name')), $this->escape($input->get('value')), $size, $maxlength);
    }

    function _renderTextarea(&$textarea)
    {
        printf('%s<input emptyok="true" name="_%s" value="%s"/>',
               $this->escape($textarea->get('label')),
               $textarea->get('name'), $textarea->get('value'));
    }

    function _renderSelect(&$select)
    {
        if ($label = $select->get('label')) {
            echo $this->escape($label) . ' ';
        }

        if ($this->hasQuirk('ow_gui_1.3')) {
            switch ($select->get('type')) {
            case 'spin':
                $type_option = 'type="spin"';
                break;

            case 'popup':
            default:
                $type_option = 'type="popup"';
                break;
            }

            echo '<select ' . $type_option . ' name="_' . $select->get('name') . '">';
        } else {
            echo '<select name="_' . $select->get('name') . '">';
        }

        $htmlchars = $select->get('htmlchars');
        foreach ($select->_options as $val) {
            $label = $htmlchars ? $val['label'] : $this->escape($val['label']);
            echo '<option value="' . $val['value'] . '">' . $label . '</option>';
        }
        echo '</select>';
    }

    function _renderRadio(&$radio)
    {
        if ($this->hasQuirk('ow_gui_1.3')) {
            // Openwave GUI extensions for WML 1.3
            printf('<select type="radio" name="_%s">', $radio->get('name'));
        } else {
            // Conventional WML (similar to Horde_Mobile_select).
            printf('<select name="_%s">', $radio->get('name'));
        }

        foreach ($radio->_buttons as $val) {
            printf('<option value="%s">%s</option>',
                   $val['value'], $this->escape($val['label']));
        }

        echo '</select>';
    }

    function _renderCheckbox(&$checkbox)
    {
        printf('<select name="_%s" multiple="true">', $checkbox->get('name'));
        printf('<option value="%s">%s</option></select>',
               $checkbox->get('value'), $this->escape($checkbox->get('label')));
    }

    function _renderSubmit(&$submit)
    {
        if ($this->hasQuirk('ow_gui_1.3')) {
            // Create <do type="button"> sequence for Openwave GUI
            // extensions WML 1.3.
            printf('<do type="button" label="%s">',
                   $this->escape($submit->get('label')));
            $tag = 'do';
        } else {
            // Create <anchor> sequence in normal WML.
            printf('<anchor title="%s">%s',
                   $this->escape($submit->get('label')),
                   $this->escape($submit->get('label')));
            $tag = 'anchor';
        }

        if ($submit->_form->get('method') == 'post') {
            printf('<go href="%s" method="post">', Horde::url($submit->_form->get('url')));

            // Value for this submit element, only if non-empty name.
            if ($submit->get('name')) {
                printf('<postfield name="%s" value="%s"/>', $submit->get('name'), $this->escape($submit->get('label')));
            }

            $defaults = $submit->_form->getDefaults();
            foreach ($defaults as $d) {
                if (array_key_exists('hidden', $d)) {
                    printf('<postfield name="%s" value="%s"/>', $d['name'], $this->escape($d['value']));
                } else {
                    printf('<postfield name="%s" value="$(_%s)"/>', $d['name'], $d['name']);
                }
            }
        } else {
            // Start with the value for this submit element.
            $query_string = $submit->get('name') . '=' . $this->escape($submit->get('label')) . '&amp;';

            $getvars = $submit->_form->getGetVars();
            foreach ($getvars as $val) {
                $query_string .= $val . '=$(_' . $val . ')&amp;';
            }

            if (substr($query_string, -5) == '&amp;') {
                $query_string = substr($query_string, 0, strlen($query_string) - 5);
            }

            printf('<go href="%s?%s">', $submit->_form->get('url'), $query_string);
        }

        echo "</go></$tag>";
    }

    function _renderTable(&$table)
    {
        // Count maximum number of columns in table.
        $max = 0;
        foreach ($table->_rows as $row) {
            $max = max($max, $row->getColumnCount());
        }
        printf('<p><table columns="%d">', $max);

        parent::_renderTable($table);

        // Terminate table.
        echo '</table></p>';
    }

    function _renderPhone(&$phone)
    {
        $title = $phone->get('title');
        $title_option = ($title ? sprintf(' title="%s"', $this->escape($title)) : '');

        printf('<a%s href="wtai://wp/mc;%s">%s</a>', $title_option,
               str_replace('+', '%2B', $phone->get('number')), $phone->get('label'));
    }

    function _renderRule(&$rule)
    {
        if ($this->hasQuirk('ow_gui_1.3')) {
            // WAP device accepts Openwave GUI extensions for WML 1.3
            $width = $rule->get('width');
            $size = $rule->get('size');

            echo '<hr' . ($width ? ' width="' . $width . '"' : '') . ($size ? ' size="' . $size . '"' : '') . ' />';
        } else {
            // WAP device does not understand <hr /> tags.
            // ==> draw some number of hyphens to create a rule
            echo '----------<br />';
        }
    }

}

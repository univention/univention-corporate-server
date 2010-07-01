<?php
/**
 * Horde_Mobile_Renderer:: output module for simple HTML and
 * Imode/Avantgo/similar devices.
 *
 * $Horde: framework/Mobile/Mobile/Renderer/html.php,v 1.28.10.11 2009-01-06 15:23:25 jan Exp $
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
class Horde_Mobile_Renderer_html extends Horde_Mobile_Renderer {

    /**
     * Properly encode characters for output to an HTML browser.
     *
     * @param string $input  Characters to encode.
     *
     * @return string  The encoded text.
     */
    function escape($input)
    {
        return @htmlspecialchars($input, ENT_COMPAT, NLS::getCharset());
    }

    /**
     * Creates the page in the appropriate markup. Depending on the
     * clients browser type pure HTML, handheldfriendly AvantGo HTML,
     * i-mode cHTML, or MML is created.
     *
     * @param Horde_Mobile $deck  The deck to render.
     */
    function render($deck)
    {
        if ($deck->_debug) {
            header('Content-Type: text/plain; charset=' . NLS::getCharset());
        } else {
            header('Content-Type: text/html; charset=' . NLS::getCharset());
        }
        header('Vary: Accept-Language');

        if (!$this->isBrowser('mml')) {
            echo "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">\n";
        }

        echo !empty($GLOBALS['language']) ? '<html lang="' . strtr($GLOBALS['language'], '_', '-') . '">' : '<html>';
        echo '<head>';

        if ($this->isBrowser('avantgo')) {
            echo '<meta name="HandheldFriendly" content="True">';
        }

        printf("<title>%s</title>\n", $this->escape($deck->get('title')));

        if ($deck->_simulator) {
            // Use simulator (mobile theme) stylesheet.
            echo Horde::stylesheetLink('horde', 'mobile');
        }

        echo '</head><body>';

        if ($deck->_simulator) {
            echo "<center><br />\n";
            // Create default device simulator table layout with
            // central CSS layout.
            echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\">\n";
            echo "<tr><td colspan=\"3\" class=\"top\">&nbsp;</td></tr>\n";
            echo "<tr><td valign=\"top\" class=\"left\">&nbsp;</td>\n";
            echo "<td valign=\"top\" class=\"display\">\n";
        }

        $divstyle = '';
        if ($this->hasQuirk('scroll_tds') && $deck->_simulator) {
            // Make content of table element scrollable (Horde_Mobile
            // simulator).
            $divstyle = ' class="simdev"';
        }
        echo '<div' . $divstyle . '>';

        if (($cnt = count($deck->_cards)) !== 0) {
            $i = 0;
            foreach ($deck->_cards as $card) {
                if ($i != 0) {
                    echo '<hr />';
                }
                $this->_renderCard($card);
                $i++;
            }
        } else {
            foreach ($deck->_elements as $page_element) {
                $this->renderElement($page_element);
            }
        }

        echo '</div>';

        if ($deck->_simulator) {
            // Display lower part of Horde_Mobile default device
            // simulator.
            echo '</td><td valign="top" class="right">&nbsp;</td></tr><tr><td colspan="3" class="bottom">&nbsp;</td></tr></table></center>';
        }

        echo '</body></html>';
    }

    function _renderCard($card)
    {
        $name = $card->get('name') ? ' name="' . $this->escape($card->get('name')) . '"' : '';
        printf('<a%s>%s</a>', $name, $card->get('title'));

        if (count($card->_softkeys)) {
            foreach ($card->_softkeys as $key) {
                echo ' | <a href="' . $key['url'] . '">' .  $this->escape($key['label']) . '</a>';
            }
        }

        // Render all tags.
        foreach ($card->_elements as $page_element) {
            $this->renderElement($page_element);
        }
    }

    function _renderLink($link)
    {
        if ($link->get('title') &&
            !$this->isBrowser('avantgo') &&
            !$this->isBrowser('imode') &&
            !$this->isBrowser('mml')) {
            $title_option = sprintf(' onmouseover="self.status=\'%s\';return true;"',
                                    $this->escape($link->get('title')));
        } else {
            $title_option = '';
        }

        $accesskey_option = '';
        if ($link->get('accesskey')) {
            if ($this->isBrowser('imode')) {
                $accesskey_option = sprintf(' accesskey="%d"', $link->get('accesskey'));
            } elseif ($this->isBrowser('mml')) {
                $accesskey_option = sprintf(' directkey="%d"', $link->get('accesskey'));
            }
        }

        printf('<a href="%s"%s%s>%s</a>',
               str_replace('&amp;amp;', '&amp;', $this->escape($link->get('url'))),
               $title_option, $accesskey_option,
               $this->escape($link->get('label')));
    }

    function _renderLinkset($linkset)
    {
        if (count($linkset->_elements)) {
            echo '<ol>';
            foreach ($linkset->_elements as $val) {
                echo '<li>';
                $this->_renderLink($val);
                echo '</li>';
            }
            echo '</ol>';
        }
    }

    function _renderText($element)
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

    function _renderImage($image)
    {
        $attributes = '';
        foreach ($image->_attributes as $attribute => $value) {
            $attributes .= sprintf(' %s="%s"', $attribute, $value);
        }
        printf('<img src="%s.png"%s />', $image->_src, $attributes);
    }

    function _renderForm($form)
    {
        printf('<form action="%s" method="%s">', $form->get('url'), $form->get('method'));
        parent::_renderForm($form);
        echo '</form>';
    }

    function _renderInput($input)
    {
        $type = 'type="' . $input->get('type') . '"';
        $size = $input->get('size') ? sprintf('size="%d"', $input->get('size')) : '';
        $maxlength = $input->get('maxlength') ? sprintf('maxlength="%d"', $input->get('maxlength')) : '';

        if ($this->isBrowser('imode')) {
            $mode = sprintf(' istyle="%d"', $input->get('mode'));
        } elseif ($this->isBrowser('mml')) {
            $mode = $this->_getMode($input->get('mode'));
        } else {
            $mode = '';
        }

        // Create HTML input.
        printf('%s <input %s name="%s" value="%s"%s%s%s/>',
               $this->escape($input->get('label')), $type,
               $this->escape($input->get('name')), $this->escape($input->get('value')), $size, $maxlength, $mode);
    }

    function _renderTextarea($textarea)
    {
        if ($this->isBrowser('imode')) {
            $mode = sprintf(' istyle="%d"', $this->mode);
        } elseif ($this->isBrowser('mml')) {
            $mode = $this->_getMode($this->mode);
        } else {
            $mode = '';
        }

        printf('%s<br /><textarea name="%s" rows="%s" cols="%s"%s>%s</textarea>',
               $this->escape($textarea->get('label')), $textarea->get('name'), $textarea->get('rows'),
               $textarea->get('cols'), $mode, $textarea->get('value'));
    }

    function _renderSelect($select)
    {
        $name = $this->escape($select->get('name'));
        echo '<label for="' . $name . '">';
        if ($label = $select->get('label')) {
            echo $this->escape($label) . ' ';
        }
        echo '<select id="' . $name . '" name="' . $name . '" size="1">';

        $htmlchars = $select->get('htmlchars');
        foreach ($select->_options as $val) {
            if ($val['value'] == $select->_value) {
                $sel = ' selected="selected"';
            } else {
                $sel = '';
            }
            $label = $htmlchars ? $val['label'] : $this->escape($val['label']);
            echo '<option' . $sel . ' value="' . $this->escape($val['value']) . '">' . $label . '</option>';
        }
        echo '</select></label>';
    }

    function _renderRadio($radio)
    {
        foreach ($radio->_buttons as $val) {
            $sel = ($val['value'] == $radio->_value) ? ' checked="checked"' : '';
            printf('<input type="radio" name="%s"%s value="%s" /> %s<br />',
                   $radio->get('name'), $sel, $val['value'],
                   $this->escape($val['label']));
        }
    }

    function _renderCheckbox($checkbox)
    {
        $state = $checkbox->isChecked() ? ' checked="checked"' : '';
        printf('<label for="%1$s"><input type="checkbox" name="%1$s" id="%1$s"%2$s value="%3$s" /> %4$s</label><br />',
               $checkbox->get('name'), $state, $checkbox->get('value'),
               $this->escape($checkbox->get('label')));
    }

    function _renderSubmit($submit)
    {
        $name = !empty($submit->_name) ? ' name="' . $submit->_name . '"' : '';
        printf('<input type="submit"%s value="%s" /><br />',
               $name, $this->escape($submit->_label));
    }

    function _renderHidden($hidden)
    {
        printf('<input type="hidden" name="%s" value="%s" />',
               $hidden->get('name'), $hidden->get('value'));
    }

    function _renderDl($dl)
    {
        echo '<dl>';

        parent::_renderDl($dl);

        // Terminate Dl.
        if ($this->isBrowser('mml')) {
            // MML has problems with the clear attribute.
            echo '</dl><br />';
        } else {
            echo '</dl><br clear="all" />';
        }
    }

    function _renderTable($table)
    {
        $border = $table->get('border');
        $padding = $table->get('padding');
        $spacing = $table->get('spacing');

        echo '<table';
        if (!is_null($border)) {
            echo ' border="' . $border . '"';
        }
        if (!is_null($padding)) {
            echo ' cellpadding="' . $padding . '"';
        }
        if (!is_null($spacing)) {
            echo ' cellspacing="' . $spacing . '"';
        }
        echo '>';

        parent::_renderTable($table);

        // Terminate table.
        if ($this->isBrowser('mml')) {
            echo '</table><br />';
        } else {
            // MML has problems with the clear attribute.
            echo '</table><br clear="all" />';
        }
    }

    function _renderPhone($phone)
    {
        if ($this->isBrowser('imode')) {
            // Create phoneto: link for i-Mode.
            printf('<p><a href="phoneto:%s">%s</a></p>',
                   $phone->get('number'), $phone->get('label'));
        } elseif ($this->isBrowser('mml')) {
            // Create tel: link for MML.
            printf('<p><a href="tel:%s">%s</a></p>',
                   $phone->get('number'), $phone->get('label'));
        } else {
            // Display phone number as plain text.
            printf('<p><big>%s</big></p>', $phone->get('label'));
        }
    }

    function _renderRule($rule)
    {
        $width = $rule->get('width');
        $size = $rule->get('size');

        echo '<hr' . ($width ? ' width="' . $width . '"' : '') . ($size ? ' size="' . $size . '"' : '') . " />\n";
    }

    function _getMode($mode)
    {
        switch ($mode) {
        case 'katakana':
            return ' mode="katakana"';

        case 'hiragana':
            return ' mode="hiragana"';

        case 'numeric':
            return ' mode="numeric"';

        case 'alpha':
        default:
            return ' mode="alphabet"';
        }
    }

}

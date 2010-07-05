<?php

require_once 'Horde/UI/VarRenderer/html.php';

/**
 * $Horde: framework/UI/UI/VarRenderer/tableset_html.php,v 1.3.2.3 2008-07-28 17:22:55 chuck Exp $
 *
 * @package Horde_UI
 * @since   Horde 3.1
 */
class Horde_UI_VarRenderer_tableset_html extends Horde_UI_VarRenderer_html {

    function _renderVarInput_tableset($form, &$var, &$vars)
    {
        $header = $var->type->getHeader();
        $name   = $var->getVarName();
        $values = $var->getValues();
        $form_name = $form->getName();
        $var_name = $var->getVarName() . '[]';
        $checkedValues = $var->getValue($vars);
        $actions = $this->_getActionScripts($form, $var);
        $function_name = 'select'  . $form_name . $var->getVarName();
        $enable = _("Select all");
        $disable = _("Select none");
        $invert = _("Invert selection");

        Horde::addScriptFile('tables.js', 'horde', true);

        $html = <<<EOT
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
<table style="width: 100%" class="sortable striped" id="tableset_' . $name . '"><thead><tr>
<th>&nbsp;</th>
EOT;

        foreach ($header as $col_title) {
            $html .= sprintf('<th class="leftAlign">%s</th>', $col_title);
        }
        $html .= '</tr></thead>';

        if (!is_array($checkedValues)) {
            $checkedValues = array();
        }
        $i = 0;
        foreach ($values as $value => $displays) {
            $checked = (in_array($value, $checkedValues)) ? ' checked="checked"' : '';
            $html .= '<tr>' .
                sprintf('<td style="text-align: center"><input id="%s[]" type="checkbox" name="%s[]" value="%s"%s%s /></td>',
                        $name,
                        $name,
                        $value,
                        $checked,
                        $actions);
            foreach ($displays as $col) {
                $html .= sprintf('<td>&nbsp;%s</td>', $col);
            }
            $html .= '</tr>' . "\n";
            $i++;
        }

        $html .= '</table>'
              . '<a href="#" onclick="' . $function_name . '(true); return false;">' . $enable . '</a>, '
              . '<a href="#" onclick="' . $function_name . '(false); return false;">' . $disable . '</a>, '
              . '<a href="#" onclick="' . $function_name . '(); return false;">' . $invert . '</a>';

        return $html;
    }

    function _renderVarDisplay_tableset($form, &$var, &$vars)
    {
        $header = $var->type->getHeader();
        $name   = $var->getVarName();
        $values = $var->getValues();
        $checkedValues = $var->getValue($vars);
        $actions = $this->_getActionScripts($form, $var);

        Horde::addScriptFile('tables.js', 'horde', true);
        $html = '<table style="width: 100%" class="sortable striped" id="tableset_' . $name . '"><thead><tr>' .
            '<th>&nbsp;</th>';
        foreach ($header as $col_title) {
            $html .= sprintf('<th class="leftAlign">%s</th>', $col_title);
        }
        $html .= '</tr></thead>';

        if (!is_array($checkedValues)) {
            $checkedValues = array();
        }
        $i = 0;
        foreach ($values as $value => $displays) {
            $checked = '[ <span style="font-weight: bold; color: '
                . (in_array($value, $checkedValues)) ? ' green">V' : 'red">X'
                . '</span> ]';
            $html .= '<tr>'.
                sprintf('<td style="text-align: center">%s</td>', $checked);
            foreach ($displays as $col) {
                $html .= '<td>&nbsp;' . $col . '</td>';
            }
            $html .= '</tr>';
            $i++;
        }

        return $html . '</table>';
    }

}

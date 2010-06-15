<?php
/**
 * Class for handling a list of categories stored in a user's
 * preferences.
 *
 * $Horde: framework/Prefs/Prefs/CategoryManager.php,v 1.8 2004/05/27 17:51:54 chuck Exp $
 *
 * Copyright 2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Prefs
 */
class Prefs_CategoryManager {

    /**
     * Get all categories.
     */
    function get()
    {
        global $prefs;

        $string = $prefs->getValue('categories');
        if (empty($string)) {
            return array();
        }

        $categories = explode('|', $string);
        asort($categories);

        return $categories;
    }

    function getSelect($id, $current = null)
    {
        global $prefs;

        $html = '<select id="' . htmlspecialchars($id) . '" name="' . htmlspecialchars($id) . '">';

        $categories = $this->get();
        if (!in_array($current, $categories) && !empty($current)) {
            $html .= '<option value="*new*' . htmlspecialchars($current) . '">' . sprintf(_("Use Current: %s"), htmlspecialchars($current)) . '</option>';
            $html .= '<option value="">----</option>';
        }

        if (!$prefs->isLocked('categories')) {
            $html .= '<option value="*new*">' . _("New Category") . "</option>\n";
            $html .= '<option value="">----</option>';
        }

        // Always add an Unfiled option.
        $html .= '<option value=""';
        $html .= empty($current) ? ' selected="selected">' : '>';
        $html .= htmlspecialchars(_("Unfiled")) . '</option>';

        foreach ($categories as $name) {
            $html .= '<option value="' . htmlspecialchars($name) . '"';
            $html .= ($name == $current) ? ' selected="selected">' : '>';
            $html .= htmlspecialchars($name) . '</option>';
        }
        $html .= '</select>';

        return $html;
    }

    function getJavaScript($formname, $elementname)
    {
        $prompt = addslashes(_("Please type the new category name:"));
        $error = addslashes(_("You must type a new category name."));

        return <<<JAVASCRIPT

<script language="JavaScript" type="text/javascript">
<!--
function checkCategory()
{
    if (document.$formname.$elementname.value == '*new*') {
        var category = window.prompt('$prompt', '');
        if (category != null && category != '') {
            document.$formname.new_category.value = category;
        } else {
            window.alert('$error');
            return false;
        }
    } else if (document.$formname.$elementname.value.indexOf('*new*') != -1) {
        document.$formname.new_category.value = document.$formname.$elementname.value.substr(5, document.$formname.$elementname.value.length);
    }

    return true;
}
//-->
</script>
JAVASCRIPT;
    }

    /**
     * Add a new category.
     *
     * @param string $category  The name of the category to add.
     *
     * @return mixed  False on failure, or the new category's name.
     */
    function add($category)
    {
        global $prefs;

        if ($prefs->isLocked('categories') || empty($category)) {
            return false;
        }

        $categories = $this->get();
        if (in_array($category, $categories)) {
            return false;
        }

        $categories[] = $category;
        $prefs->setValue('categories', implode('|', $categories));

        return $category;
    }

    /**
     * Delete a category.
     *
     * @param string $category  The category to remove.
     *
     * @return boolean  True on success, false on failure.
     */
    function remove($category)
    {
        global $prefs;

        if ($prefs->isLocked('categories')) {
            return false;
        }

        $categories = $this->get();

        $key = array_search($category, $categories);
        if ($key === false) {
            return $key;
        }

        unset($categories[$key]);
        $prefs->setValue('categories', implode('|', $categories));

        // Remove any color settings for $category.
        $colors = $this->colors();
        unset($colors[$category]);
        $this->setColors($colors);

        return true;
    }

    /**
     * Returns the color for each of the user's categories.
     *
     * @return array  A list of colors, key is the category name,
     *                                  value is the HTML color code.
     */
    function colors()
    {
        global $prefs;

        /* Default values that can be overridden but must always be
         * present. */
        $colors['_default_'] = '#FFFFFF';
        $colors['_unfiled_'] = '#DDDDDD';

        $pairs = explode('|', $prefs->getValue('category_colors'));
        foreach ($pairs as $pair) {
            if (!empty($pair)) {
                list($category, $color) = explode(':', $pair);
                $colors[$category] = $color;
            }
        }

        $colors[''] = $colors['_unfiled_'];

        return $colors;
    }

    function setColor($category, $color)
    {
        $colors = $this->colors();
        $colors[$category] = $color;
        $this->setColors($colors);
    }

    function setColors($colors)
    {
        global $prefs;

        $pairs = array();
        foreach ($colors as $category => $color) {
            if (!empty($category)) {
                $pairs[] = "$category:$color";
            }
        }

        $prefs->setValue('category_colors', implode('|', $pairs));
    }

}

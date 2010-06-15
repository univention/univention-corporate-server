<?php
if ($prefs->getValue('show_legend') && count($GLOBALS['display_calendars'])) {
    $html = '<tr><td class="light" align="center">';
    $html .= '<table border="0" cellpadding="0" cellspacing="4"><tr>';

    $colors = $cManager->colors();

    // Special handling for Unfiled events.
    $categoryColor = isset($colors['_unfiled_']) ? $colors['_unfiled_'] : $colors['_default_'];
    $html .= '<td class="legend-eventbox" style="background-color: ' . $categoryColor . '; ';
    $html .= 'border-color: ' . Kronolith::borderColor($categoryColor) . '"><span class="event">' . _("Unfiled") . '</span></td>';

    $categories = $cManager->get();
    foreach ($categories as $category) {
        $categoryColor = isset($colors[$category]) ? $colors[$category] : $colors['_default_'];
        $html .= '<td class="legend-eventbox" style="background-color: ' . $categoryColor . '; ';
        $html .= 'border-color: ' . Kronolith::borderColor($categoryColor) . '"><span class="event">' . htmlspecialchars($category) . '</span></td>';
    }
    $html .= "</tr>\n";

    echo $html . "</table></td></tr>\n";
}

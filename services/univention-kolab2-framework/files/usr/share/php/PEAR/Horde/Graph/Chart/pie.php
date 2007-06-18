<?php
/**
 * Pie graph implementation for the Horde_Graph package.
 *
 * $Horde: framework/Graph/Graph/Chart/pie.php,v 1.10 2004/05/06 20:24:43 chuck Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Graph
 */
class Horde_Graph_Chart_pie {

    var $graph;

    var $_dataset;
    var $_padding = 20;
    var $_outline = true;
    var $_colors = array('tan', 'palegoldenrod', 'olivedrab', 'blue', 'red', 'green', 'yellow',
                         'orange', 'gray', 'purple');
    /**
      "255,153,0",
      "0,204,153",
      "204,255,102",
      "255,102,102",
      "102,204,255",
      "204,153,255",
      "255,0,0",
      "51,0,255",
      "255,51,153",
      "204,0,255",
      "255,255,51",
      "51,255,51",
      "255,102,0");
    */

    function Horde_Graph_Chart_pie(&$graph, $params)
    {
        $this->graph = &$graph;

        foreach ($params as $param => $value) {
            $key = '_' . $param;
            $this->$key = $value;
        }
    }

    function draw()
    {
        $data = $this->graph->_data['y'][$this->_dataset];

        // Initialize some variables.
        $diameter = min($this->graph->_graphWidth, $this->graph->_graphHeight) - ($this->_padding * 2);
        $radius = $diameter / 2;
        $count = count($data);
        $xcenter = $this->graph->_graphLeft + $this->_padding + ($this->graph->_graphWidth / 2);
        $ycenter = $this->graph->_graphTop + $this->_padding + ($this->graph->_graphHeight / 2);

        // Calculate the sum of all slices.
        $sum = 0;
        foreach ($data as $x) {
            $sum += $x;
        }

        // Convert each slice into the corresponding percentage of a
        // 360-degree circle.
        $degCount = 0;
        $slices = array();
        $degrees = array();
        foreach ($data as $i => $y) {
            if ((($y / $sum) * 360) > 0) {
                $degrees[$degCount] = ($y / $sum) * 360;
                $slices[$degCount] = $y;
                $names[$degCount] = isset($this->graph->_data['x'][$i]) ? $this->graph->_data['x'][$i] : '';
                $degCount++;
            }
        }

        // Draw the baseline.
        if ($count > 1) {
            $last_angle = 0;
            $count = count($degrees);
            for ($z = 0; $z < $count; $z++) {
                // Calculate and draw arcs corresponding to each
                // slice.
                $cz = $z % count($this->_colors);
                $this->graph->img->arc($xcenter, $ycenter, $radius, $last_angle, ($last_angle + $degrees[$z]),
                                       $this->_outline ? 'black' : $this->_colors[$cz], $this->_colors[$cz]);
                $last_angle = $last_angle + $degrees[$z];
            }
        } else {
            $this->graph->img->circle($xcenter, $ycenter, $radius, 'black', $this->_colors[0]);
        }

        // Create the color key and slice labels.
        $yBase = $this->graph->_graphTop;
        $xBase = 5;
        $max = strlen((string)max($data));
        for ($z = 0; $z < $degCount; $z++) {
            $cz = $z % count($this->_colors);
            $percent = ($degrees[$z] / 360) * 100;
            $percent = round($percent, 2);
            $yBase += 15;

            $this->graph->img->rectangle($xBase, $yBase, 12, 12, 'black', $this->_colors[$cz]);
            if ($slices[$z] >= 1000 && $slices[$z] < 1000000) {
                $slices[$z] = $slices[$z] / 1000;
                $slices[$z] = $slices[$z] . 'k';
            }
            $repeat = $max - strlen($slices[$z]);
            if ($repeat < 0) {
                $repeat = 0;
            }
            $slices[$z] = str_repeat(' ', $repeat) . $slices[$z];

            $this->graph->img->text($slices[$z], $xBase + 20, ($yBase + 1));

            $label = $names[$z] . ' (' . $percent . '%)';
            if (strlen($label) > 20) {
                $labels = explode("\n", wordwrap($label, 20));
                foreach ($labels as $i => $label) {
                    if ($i > 0) {
                        $yBase += 15;
                    }
                    $this->graph->img->text($label, $xBase + 35 + ($max * 4), ($yBase + 1));
                }
            } else {
                $this->graph->img->text($label, $xBase + 35 + ($max * 4), ($yBase + 1));
            }
        }
    }

}

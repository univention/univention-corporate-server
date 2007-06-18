<?php

require_once 'Horde/Graph/Plot/bar.php';

/**
 * Grouped bar graph implementation for the Horde_Graph package.
 *
 * $Horde: framework/Graph/Graph/Plot/bargrouped.php,v 1.1 2004/05/06 21:14:56 chuck Exp $
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
class Horde_Graph_Plot_bargrouped extends Horde_Graph_Plot_bar {

    var $_step = .5;
    var $_colors = array();
    var $_datasets = array();

    function draw()
    {
        // Calculate the starting offset for each bar, from which we
        // move it over by $this->_step.
        $datasets = count($this->_datasets);
        $globalOffset = $this->_offset - (($this->_step * ($datasets - 1)) / 2);

        for ($i = 0; $i < $datasets; $i++) {
            // Calculate the offset of this set of bars.
            $this->_offset = $globalOffset + ($this->_step * $i);

            // Set bar parameters that change per-group.
            if (isset($this->_colors[$i])) {
                $this->_color = $this->_colors[$i];
            }
            $this->_dataset = $this->_datasets[$i];

            // Draw this dataset.
            parent::draw();
        }
    }

}

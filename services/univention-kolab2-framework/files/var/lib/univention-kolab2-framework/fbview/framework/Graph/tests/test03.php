<?php
/**
 * $Horde: framework/Graph/tests/test03.php,v 1.5 2004/05/06 20:56:43 chuck Exp $
 *
 * @package Horde_Graph
 */

require_once dirname(__FILE__) . '/../Graph.php';

$graph = &new Horde_Graph(array('height' => 400, 'width' => 400));

$graph->set('title', '3 scatters');
$graph->set('ylabel', 'Some Parameters');
$graph->set('xlabel', 'Day of the Week');

$graph->addXData(array('Fri', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri'));
$data1 = $graph->addYData(array(8.610, 7.940, 3.670, 3.670, 6.940, 8.650));
$data2 = $graph->addYData(array(1.456, 3.001, 5.145, 2.050, 1.998, 1.678));
$data3 = $graph->addYData(array(4.896, 4.500, 4.190, 3.050, 2.888, 3.678));

$graph->addPlot('scatter', array('dataset' => $data3, 'shape' => 'rectangle', 'color' => 'blue'));
$graph->addPlot('scatter', array('dataset' => $data2, 'shape' => 'triangle', 'color' => 'green'));
$graph->addPlot('scatter', array('dataset' => $data1, 'shape' => 'circle', 'color' => 'red'));

$graph->draw();

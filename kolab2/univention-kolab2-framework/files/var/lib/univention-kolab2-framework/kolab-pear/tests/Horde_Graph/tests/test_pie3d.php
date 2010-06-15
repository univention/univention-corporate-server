<?php
/**
 * $Horde: framework/Graph/tests/test_pie3d.php,v 1.1 2004/05/06 20:57:39 chuck Exp $
 *
 * @package Horde_Graph
 */

require_once dirname(__FILE__) . '/../Graph.php';

$graph = &new Horde_Graph(array('height' => 400, 'width' => 400));
$graph->set('title', '3D Pie chart');
$graph->set('imgType', 'svg');

$graph->addXData(array('Fri', 'Mon'));
$data1 = $graph->addYData(array(8, 5, 4, 10, 3, 9));

$graph->addChart('pie3d', array('dataset' => $data1));

$graph->draw();

<?php
/**
 * $Horde: framework/Graph/tests/test06.php,v 1.6 2004/05/06 20:56:43 chuck Exp $
 *
 * @package Horde_Graph
 */

require_once dirname(__FILE__) . '/../Graph.php';

$graph = &new Horde_Graph(array('height' => 400, 'width' => 400));
$graph->set('title', 'Pie chart');
$graph->set('imgType', 'svg');

$graph->addXData(array('Fri', 'Mon'));
$data1 = $graph->addYData(array(8, 5, 4, 10, 3, 9));

$graph->addChart('pie', array('dataset' => $data1,
                              'outline' => false));

$graph->draw();

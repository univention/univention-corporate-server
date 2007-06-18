<?php
    //
    //  $Id: Dynamic_DBnested.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
    //

//ini_set('include_path',realpath(dirname(__FILE__).'/../../').':'.realpath(dirname(__FILE__).'/../../../includes').':'.ini_get('include_path'));
//ini_set('error_reporting',E_ALL);

    require_once('Tree/Tree.php');

#    $tree = Tree::setupDynamic( 'DBnested' , 'mysql://root@localhost/test' , array('table'=>'nestedTree') );
#   OR
    $tree = Tree::setup( 'Dynamic_DBnested' , 'mysql://root@localhost/test' , array('table'=>'nestedTree') );

    $show[] = '$tree->getRoot()';
    $show[] = '$tree->getElement( 1 )';
    $show[] = '$tree->getChild( 1 )';
    $show[] = '$tree->getPath( 7 )';
    $show[] = '$tree->getPath( 2 )';
    $show[] = '$tree->add( array("name"=>"c0") , 5 )';
    $show[] = '$tree->remove( $res )';  // remove the last element that was added in the line before :-)
    $show[] = '$tree->getRight( 5 )';
    $show[] = '$tree->getLeft( 5 )';
    $show[] = '$tree->getChildren( 1 )';
    $show[] = '$tree->getParent( 2 )';
    $show[] = '$tree->getNext( 2 )';
    $show[] = '$tree->getNext( 4 )';
    $show[] = '$tree->getNext( 8 )';
    $show[] = '$tree->getPrevious( 2 )';
    $show[] = '$tree->getPrevious( 4 )';
    $show[] = '$tree->getPrevious( 8 )';
    $show[] = '$tree->getPreviousId( 8 )';

    $show[] = '$tree->move( 4,3 )';


    foreach( $show as $aRes )
    {
        print("<b>$aRes</b><br>");
        eval("\$res=".$aRes.';');
        if( $res == false )
            print "false";
        else
            print_r($res);

        print('<br><br>');
    }


?>

<a href="http://research.calacademy.org/taf/proceedings/ballew/sld029.htm">the tree structure visualisation</a>

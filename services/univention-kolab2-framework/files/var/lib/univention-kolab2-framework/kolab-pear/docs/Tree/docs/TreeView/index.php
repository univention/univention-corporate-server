<?php
    //
    //  $Id: index.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
    //
ini_set('include_path',realpath(dirname(__FILE__).'/../../../').':'.realpath(dirname(__FILE__).'/../../../../includes').':'.ini_get('include_path'));
ini_set('error_reporting',E_ALL);

    ##################################################
    #
    #       init template engine
    #
    // you need the template class from http://sf.net/projects/simpltpl
    if (!@include('HTML/Template/Xipe.php')) {
        print   'sorry, you need the template class PEAR::HTML_Template_Xipe<br>'.
                'or if i have time i put the examples <a href="http://os.visionp.de/">here online</a>';
        die();
    }
    require_once('HTML/Template/Xipe/Filter/TagLib.php');
    $options = array(   'templateDir'   => dirname(__FILE__) );
    $tpl = new HTML_Template_Xipe($options);


    ##################################################
    #
    #       actual tree stuff, using Dynamic_DBnested
    #
    require_once('Tree/Tree.php');
    $tree = Tree::setup( 'Dynamic_DBnested' , 'mysql://root@localhost/test' , array('table'=>'Tree_Nested') );
    
    if( @$_REQUEST['action_add'] )
    {
        $methodCall = "tree->add( {$_REQUEST['newData']} , {$_REQUEST['parentId']} , {$_REQUEST['prevId']} )";
        $result = $tree->add( $_REQUEST['newData'] , $_REQUEST['parentId'] , $_REQUEST['prevId'] );
    }

    if( @$_REQUEST['action_remove'] )
    {
        $methodCall = "$tree->remove( {$_REQUEST['removeId']} )";
        $result = $tree->remove( $_REQUEST['removeId'] );
    }

    if( @$_REQUEST['action_update'] )
    {
        $methodCall = "tree->update( {$_REQUEST['updateId']} , {$_REQUEST['updateData']} )";
        $result = $tree->update( $_REQUEST['updateId'] , $_REQUEST['updateData'] );
    }

    if( @$_REQUEST['action_move'] )
    {
        $methodCall = "tree->move( {$_REQUEST['move_id']} , {$_REQUEST['move_newParentId']} , {$_REQUEST['move_newPrevId']} )";
        $result = $tree->move( $_REQUEST['move_id'] , $_REQUEST['move_newParentId'] , $_REQUEST['move_newPrevId'] );
    }

    $methodFailed = false;
    if( @PEAR::isError($result) )
        $methodFailed = true;

    $fid = @$_REQUEST['fid'];
    if( !$fid )
        $fid = $tree->getRootId();

    $path = $tree->getPath( $fid );
    $children = $tree->getChildren( $fid );

    ##################################################
    #
    #       actual tree stuff to show the entire tree using Memory_DBnested
    #
    require_once('Tree/Tree.php');
    $memTree = Tree::setup( 'Memory_DBnested' , 'mysql://root@localhost/test' , 
                            array('table'=>'Tree_Nested') );

    $memTree->setup();
    $entireTree = $memTree->getNode();
    $treeDepth = $memTree->getDepth();

    $tpl->compile('index.tpl');
    include($tpl->compiledTemplate);
?>

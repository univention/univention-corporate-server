<?php
    //
    //  $Id: index.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
    //
//ini_set('include_path',realpath(dirname(__FILE__).'/../../../').':'.realpath(dirname(__FILE__).'/../../../../includes').':'.ini_get('include_path'));
//ini_set('error_reporting',E_ALL);

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

    require_once('HTML/Template/Xipe/Filter/Modifier.php');
    $modifiers = new HTML_Template_Xipe_Filter_Modifier($tpl->options);
    $tpl->registerPrefilter(array(&$modifiers,'imgSrc'),
                            array(dirname(__FILE__),'http://'.$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF'])));


    // session stuff to save the opened folders etc.
    session_start();
    if(!session_is_registered('session'))
    {
        $session = new stdClass;    // standard PHP-class constructor
        session_register('session');
        $session->data = array();
        $session->use = 'Filesystem';
    }
    else    // since the class is read from the session it is not automatically made global
    {
        $session = &$_SESSION['session'];
    }

    // set the source to use
    if( @$_REQUEST['use_DB'] )
        $session->use = 'DB';
    if( @$_REQUEST['use_Filesystem'] )
        $session->use = 'Filesystem';
    if( @$_REQUEST['use_XML'] )
        $session->use = 'XML';
    if( @$_REQUEST['use_Array'] )
        $session->use = 'Array';

    ##################################################
    #
    #       actual tree stuff
    #
    define('TABLE_TREE','Tree_Nested');
    define('DB_DSN','mysql://root@localhost/test');

    require_once('treeClass.php');
    if( $session->use == 'DB' )
    {
        $options = array( 'table' => TABLE_TREE , 'order' =>  'name');
        $tree = new treeClass( 'DBnested' , DB_DSN , $options );
    }
    if( $session->use == 'Filesystem' )
    {
        # to let it work on the filesystem :-)
        $options = array( 'order' =>  'name');
        $tree = new treeClass( 'Filesystem' , dirname(__FILE__).'/tmp' , $options );
    }
    if( $session->use == 'XML' )
    {
        $tree = new treeClass( 'XML' , dirname(__FILE__).'/config.xml' );
    }
    if( $session->use == 'Array' )
    {
        // the actual data for the tree, they have to have the given structure
        $arrayData = array( 'name'=>'Root',
                            'children'=>array(
                                array('name'=>'dir1'),
                                array('name'=>'dir2',
                                    'children'=>array(
                                        array('name'=>'dir2_1'),
                                        array('name'=>'dir2_2'),
                                        )
                                    ),
                                array('name'=>'dir3')
                            )
                           );

        // any on an array
        $options = array( 'order' =>  'name');
        $tree = new treeClass( 'Array' , $arrayData , $options );
    }





    if( PEAR::isError($res=$tree->setup()) )
    {
        $methodFailed = true;
        $results[] = $res;
    }

    $tree->setRemoveRecursively();

    // detect action

    if( @$_REQUEST['action_copy'] || @$_REQUEST['action_copy_x'] ||
        @$_REQUEST['action_cut'] || @$_REQUEST['action_cut_x'] )
    {
        if( @$_REQUEST['action_copy'] || @$_REQUEST['action_copy_x'])      $session->action = 'copy';
        if( @$_REQUEST['action_cut'] || @$_REQUEST['action_cut_x'] )       $session->action = 'cut';

        if( is_array($_REQUEST['selectedNodes']) && sizeof($_REQUEST['selectedNodes']))
        {
            $session->data = $_REQUEST['selectedNodes'];
        }
        else
        {
            $session->action = '';
        }
    }

    if( @$_REQUEST['action_paste'] || @$_REQUEST['action_paste_x'] )
    {
        if( is_array($session->data) && sizeof($session->data))
        {
            if( $session->action == 'copy' )
            {
                if( is_array($_REQUEST['selectedNodes']) && sizeof($_REQUEST['selectedNodes']))
                {
                    $dest = $_REQUEST['selectedNodes'];
                    $sources = $session->data;
                    foreach( $sources as $aSrc )
                    {
                        foreach( $dest as $aDest )
                        {
                            $methodCalls[] = "tree->copy( $aSrc , $aDest )";
                            $results[] = $tree->copy( $aSrc , $aDest );
                        }
                    }

                    #$results = 'Sorry COPY is not implemented yet :-(';
                    $session->data = array();
                    unset($session->action);
                    $tree->setup();
                }
                else
                {
                    $methodFailed = true;
                    $results = 'Please choose destination folder(s) to paste to!';
                }
            }

            if( $session->action == 'cut')
            {
                if( !$_REQUEST['moveDest'] )
                {
                    $methodFailed = true;
                    $results = 'Please choose a destination to paste to!';
                }
                else
                {
                    foreach( $session->data as $aNodeId )
                    {
                        $methodCalls[] = "tree->move( $aNodeId , {$_REQUEST['moveDest']} )";
                        $results[] = $tree->move( $aNodeId , $_REQUEST['moveDest'] );
                    }
                    $session->data = array();
                    unset($session->action);
                    $tree->setup();
                }
            }
        }
    }

    if( (@$_REQUEST['action_delete'] || @$_REQUEST['action_delete_x']) &&
        is_array($_REQUEST['selectedNodes']) && sizeof($_REQUEST['selectedNodes']) )
    {
        $rootId = $tree->getRootId();
        foreach( $_REQUEST['selectedNodes'] as $aNodeId )
        {
            if( $rootId == $aNodeId )
            {
                $methodCalls[] = 0;
                $results[] = 'Cant remove Root with this application!';
                $methodFailed = true;
            }
            else
            {
                $methodCalls[] = "tree->remove( $aNodeId )";
                $res = $tree->remove( $aNodeId );
                if(PEAR::isError($res))
                    $methodFailed = true;
                $results[] = $res;
            }
        }
        $session->data = array();
        unset($session->action);
        $tree->setup();
    }


    if( @$_REQUEST['action_add'] &&
        is_array($_REQUEST['selectedNodes']) && sizeof($_REQUEST['selectedNodes']) &&
        $_REQUEST['newFolder'] )
    {
        foreach( $_REQUEST['selectedNodes'] as $aNodeId )
        {
            $methodCalls[] = "tree->add( {$_REQUEST['newFolder']} , $aNodeId )";
            $res = $tree->add( $_REQUEST['newFolder'] , $aNodeId );
            if(PEAR::isError($res))
                $methodFailed = true;
            $results[] = $res;
        }
        $session->data = array();
        unset($session->action);
        $tree->setup();
    }


    $allVisibleFolders = $tree->getAllVisible();

    if( !@is_array($_REQUEST['selectedNodes']) )
        $_REQUEST['selectedNodes'] = array();

    ##################################################
    #
    #       show the template
    #
    $tpl->compile('index.tpl');
    include($tpl->compiledTemplate);
?>

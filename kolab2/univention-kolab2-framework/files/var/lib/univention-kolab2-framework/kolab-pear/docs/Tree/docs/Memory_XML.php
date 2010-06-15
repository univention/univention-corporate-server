<?php
    //
    //  $Id: Memory_XML.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
    //

//ini_set('include_path',realpath(dirname(__FILE__).'/../../').':'.realpath(dirname(__FILE__).'/../../../includes').':'.ini_get('include_path'));
//ini_set('error_reporting',E_ALL);
    /**
    *   this is a helper function, so i dont have to write so many prints :-)
    *   @param  array   $para   the result returned by some method, that will be dumped
    *   @param  string  $string the explaining string
    */
    function dumpHelper( $para , $string='' )
    {
        global $tree;

        print '<i><u><font color="#008000">'.$string.'</font></u></i><br>';
        // this method dumps to the screen, since print_r or var_dump dont
        // work too good here, because the inner array is recursive
        // well, it looks ugly but one can see what is meant :-)
        $tree->varDump($para);
        print '<br>';

    }

    /**
    *   dumps the entire structure nicely
    *   @param  string  $string the explaining string
    */
    function dumpAllNicely( $string='' )
    {
        global $tree;

        print '<i><u><font color="#008000">'.$string.'</font></u></i><br>';
        $all = $tree->getNode();   // get the entire structure sorted as the tree is, so we can simply foreach through it and show it
        foreach( $all as $aElement )
        {
            for( $i=0 ; $i<$aElement['level'] ; $i++)
                print '&nbsp; &nbsp; ';
            print '<b>'.$aElement['name'].'</b> ===&gt; ';

            // you can also show all the content, using this
            // $tree->varDump(array($aElement));
            // i just didnt, since it takes up more then the entire line, and its unreadable :-)

            print 'attributes - ';
            print_r($aElement['attributes']);
            print '<br>';

        }
        print '<br>';

    }


    /*

        This example demonstrates how to manage trees
        that are saved in an XML-file

        it reads out the entire file upon calling the method
        'setup', then you can work on the tree in whichever way
        you want, just have a look at the examples
        there are different ways to achieve things,
        i will try to demonstrate (all of) them     
        
        NOTE: for referening the XML-Nodes currently everything has to 
        be lower case, 
            SimpleTemplate/preFilter
        should be                   
            simpletemplate/prefilter

    */

    require_once('Tree/Tree.php');

    // calling 'setupMemory' means to retreive a class, which works on trees,
    // that are temporarily stored in the memory, in an array
    // this means the entire tree is available at all time
    // consider the resource usage and it's not to suggested to work
    // on huge trees (upto 1000 elements it should be ok, depending on your environment and requirements)
    // using 'setupMemory'
    $tree = Tree::setupMemory(  'XML',          // use the XML class to read an xml file
                                'config.xml'    // the DSN
                             );

    // methods 'add' 'remove' and so on are not implemented yet, you can only read the tree for now
    // and navigate inside of it

    // call 'setup', to build the inner array, so we can work on the structure using the
    // given methods
    $tree->setup();

    dumpAllNicely( 'dump all after "$tree-&gt;setup"' );

    // get the path of the last inserted element
    print 'id='.$id = $tree->getIdByPath('simpletemplate/options/delimiter');
    dumpHelper( $tree->getPath( $id ) , 'dump the path from "simpletemplate/options/delimiter"' );

    $id = $tree->getIdByPath('simpletemplate/options');
    dumpHelper( array($tree->getParent($id)) , 'dump the parent of "simpletemplate/options"' );
    // you can also use:    $tree->data[$id]['parent']

    $id = $tree->getIdByPath('simpletemplate');
    dumpHelper( array($tree->getChild($id)) , 'dump the child of "simpletemplate"' );
    // you can also use:    $tree->data[$id]['child']

    $id = $tree->getIdByPath('simpletemplate/prefilter');
    dumpHelper( $tree->getChildren($id) , 'dump the children of "simpletemplate/prefilter"' );
    // you can also use:    $tree->data[$id]['children']

    $id = $tree->getIdByPath('simpletemplate/options');
    dumpHelper( array($tree->getNext($id)) , 'dump the "next" of "simpletemplate/options"' );
    // you can also use:    $tree->data[$id]['next']

    $id = $tree->getIdByPath('simpletemplate/prefilter');
    dumpHelper( array($tree->getPrevious($id)) , 'dump the "previous" of "simpletemplate/prefilter"' );
    // you can also use:    $tree->data[$id]['previous']


    $id = $tree->getIdByPath('simpletemplate/preFilter');
    $element = $tree->data[$id]['child']['next']['next']; // refer to the third child of 'SimpleTemplate/preFilter/register'
    dumpHelper( $element['id'] , 'demo of using the internal array, for referencing tree-nodes' );

/*
NOT IMPLEMENTED YET

    $id = $tree->getIdByPath('myElement/anotherSubElement');
    $tree->move( $id , 0 );
    $tree->setup(); // rebuild the structure again, since we had changed it
    dumpAllNicely( 'dump all, after "myElement/anotherSubElement" was moved under the root' );

    $moveId = $tree->getIdByPath('myElement');
    $id = $tree->getIdByPath('anotherSubElement');
    $tree->move( $moveId , $id );
    $tree->setup(); // rebuild the structure again, since we had changed it
    dumpAllNicely( 'dump all, after "myElement" was moved under the "anotherSubElement"' );


    $tree->setRemoveRecursively(true);
    $tree->remove(0);
    print '<font color="red">ALL ELEMENTS HAVE BEEN REMOVED (uncomment this part to keep them in the DB after running this test script)</font>';
*/
?>

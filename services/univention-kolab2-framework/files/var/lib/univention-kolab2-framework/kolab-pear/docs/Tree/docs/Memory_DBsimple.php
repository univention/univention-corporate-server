<?php
    //
    //  $Id: Memory_DBsimple.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
    //

//ini_set('include_path',realpath(dirname(__FILE__).'/../../').':'.realpath(dirname(__FILE__).'/../../../includes').':'.ini_get('include_path'));
//ini_set('error_reporting',E_ALL);

    /**
    *   this is a helper function, so i dont have to write so many prints :-)
    *   @param  array   $para   the result returned by some method, that will be dumped
    *   @param  string  $string the explaining string
    */
    function dumpHelper( $para , $string='' , $addArray=false )
    {
        global $tree,$element;

        if( $addArray )
            eval( "\$res=array(".$para.');' );
        else
            eval( "\$res=".$para.';' );

        print '<b>'.$para.' </b><i><u><font color="#008000">'.$string.'</font></u></i><br>';
        // this method dumps to the screen, since print_r or var_dump dont
        // work too good here, because the inner array is recursive
        // well, it looks ugly but one can see what is meant :-)
        $tree->varDump($res);
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
            print $aElement['name'].' ===&gt; ';
            $tree->varDump(array($aElement));
        }
        print '<br>';

    }


    /*

        use this to build the db table

        CREATE TABLE test_tree (
            id int(11) NOT NULL auto_increment,
            parentId int(11) NOT NULL default '0',
            name varchar(255) NOT NULL default '',
            PRIMARY KEY  (id)
        )


        This example demonstrates how to manage trees
        that are saved in a DB, it uses a very simple
        DB-structure, not nested trees (ok, that sucks, but it can be implemented :-) )

        it reads out the entire tree upon calling the method
        'setup', then you can work on the tree in whichever way
        you want, just have a look at the examples
        there are different ways to achieve things,
        i will try to demonstrate (all of) them

    */

    require_once('Tree/Tree.php');

    // define the DB-table where the data shall be read from
    $options = array(   'table' =>  'test_tree',
                        'order' =>  'id'    // when reading the data from the db sort them by id, this is only for ensuring
                                            // for 'getNext' of "myElement/subElement" in this example to find "myElement/anotherSubElement"
                                            // you can simply sort it by "name" and it would be in alphabetical order
                    );

    // calling 'setupMemory' means to retreive a class, which works on trees,
    // that are temporarily stored in the memory, in an array
    // this means the entire tree is available at all time
    // consider the resource usage and it's not to suggested to work
    // on huge trees (upto 1000 elements it should be ok, depending on your environment and requirements)
    // using 'setupMemory'
    $tree = Tree::setupMemory(  'DBsimple',         // use the simple DB schema
                                'mysql://root@localhost/test',  // the DSN
                                $options);          // pass the options we had assigned up there

    // add a new root element in the tree
    $parentId = $tree->add(array( 'name'=>'myElement'));

    // add an element under the new element we added
    $id = $tree->add(array( 'name'=>'subElement') , $parentId );

    // add another element under the parent element we added
    $id = $tree->add(array( 'name'=>'anotherSubElement') , $parentId );

    // call 'setup', to build the inner array, so we can work on the structure using the
    // given methods
    $tree->setup();

    dumpAllNicely( 'dump all after creation' );

    // get the path of the last inserted element
    dumpHelper( '$tree->getPath( '.$id.' )' , 'dump the path from "myElement/anotherSubElement"' );

    print "tree->getIdByPath('myElement/subElement')=".$id = $tree->getIdByPath('myElement/subElement');
    dumpHelper( '$tree->getParent('.$id.')' , 'dump the parent of "myElement/subElement"' , true );
    // you can also use:    $tree->data[$id]['parent']

    $id = $tree->getIdByPath('myElement');
    dumpHelper( '$tree->getChild('.$id.')' , 'dump the child of "myElement"' , true );
    // you can also use:    $tree->data[$id]['child']

    $id = $tree->getIdByPath('myElement');
    dumpHelper( '$tree->getChildren('.$id.')' , 'dump the children of "myElement"' );
    // you can also use:    $tree->data[$id]['children']

    $id = $tree->getIdByPath('myElement/subElement');
    dumpHelper( '$tree->getNext('.$id.')' , 'dump the "next" of "myElement/subElement"' , true );
    // you can also use:    $tree->data[$id]['next']

    $id = $tree->getIdByPath('myElement/anotherSubElement');
    dumpHelper( '$tree->getPrevious('.$id.')' , 'dump the "previous" of "myElement/anotherSubElement"' , true );
    // you can also use:    $tree->data[$id]['previous']

    $id = $tree->getIdByPath('myElement');
    $element = $tree->data[$id]['child']['next']['parent']; // refer to yourself again, in a very complicated way :-)
    dumpHelper( '$element[\'id\']' , 'demo of using the internal array, for referencing tree-nodes, see the code' );

    $id = $tree->getIdByPath('myElement');
    $element = $tree->data[$id]['child']['next']; // refer to the second child of 'myElement'
    dumpHelper( '$element[\'id\']' , 'demo2 of using the internal array, for referencing tree-nodes, see the code' );

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

?>

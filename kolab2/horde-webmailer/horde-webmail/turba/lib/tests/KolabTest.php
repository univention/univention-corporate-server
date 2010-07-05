<?php

require_once dirname(__FILE__) . '/KolabTestBase.php';

/**
 * $Horde: turba/lib/tests/KolabTest.php,v 1.1.2.2 2008-11-07 15:03:33 selsky Exp $
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Turba
 * @subpackage UnitTests
 */
class Turba_KolabTest extends Turba_KolabTestBase {

    /**
     * Test setup.
     *
     * @return NULL
     */
    public function setUp()
    {
        $this->prepareTurba();

        $this->_kolab = &new Kolab();
    }

    function testBug5476()
    {
        /* Open our addressbook */
        $this->_kolab->open('INBOX/Contacts', 1);

        $object = array(
            'uid' => 1,
            'given-name' => 'test',
            'last-name' => 'test',
            'full-name' => 'test  test',
        );

        // Save the contact
        $this->_kolab->_storage->save($object);

        $object = array(
            'uid' => 2,
            'given-name' => 'test2',
            'last-name' => 'test2',
            'full-name' => 'test2  test2',
        );

        // Save the contact
        $this->_kolab->_storage->save($object);

        // Check that the driver can be created
        $turba = Turba_Driver::singleton('wrobel@example.org');
        $this->assertNoError($turba);

        $result = $turba->search(array(), array('last-name'));
        $this->assertNoError($result);
        $this->assertEquals(2, $result->count());

        $turba = Turba_Driver::singleton('INBOX%2Ftest2');
        $result = $turba->search(array(), array('last-name'));

        $this->assertEquals(0, $result->count());
    }

    function testPhoto()
    {
        /* Open our addressbook */
        $this->_kolab->open('INBOX/Contacts', 1);

        $object = array(
            'uid' => 1,
            'given-name' => 'photo',
            'last-name' => 'photo',
            'full-name' => 'photo photo',
            'photo' => 'abcd',
            'phototype' => 'image/jpeg',
        );

        // Save the contact
        $turba = Turba_Driver::singleton('wrobel@example.org');
        $this->assertNoError($turba);

        $this->assertNoError($turba->_add($object));

        $list = Kolab_List::singleton();
        $share = &$list->getByShare('INBOX/Contacts', 'contact');
        $data = &$share->getData();
        $object = $data->getObject('1');
        $this->assertTrue(isset($object['_attachments'][$object['picture']]));
        $attachment = $data->getAttachment($object['_attachments'][$object['picture']]['key']);
        $this->assertEquals("abcd\n", $attachment);
    }

    function testAttachments()
    {
        /* Open our addressbook */
        $this->_kolab->open('INBOX/Contacts', 1);

        $object = array(
            'uid' => 'a',
            'given-name' => 'atc',
            'last-name' => 'atc',
            'full-name' => 'atc atc',
        );

        // Save the contact
        $turba = Turba_Driver::singleton('wrobel@example.org');
        $this->assertNoError($turba);

        $this->assertNoError($turba->_add($object));

        $contact = $turba->getObject('a');
        $this->assertNoError($contact);

        $list = Kolab_List::singleton();
        $share = &$list->getByShare('INBOX/Contacts', 'contact');
        $data = &$share->getData();

        $atc1 = Util::getTempFile();
        $fh = fopen($atc1, 'w');
        fwrite($fh, 'test');
        fclose($fh);

        $info = array('tmp_name' => $atc1,
                      'name' => 'test.txt');
        $this->assertNoError($contact->addFile($info));

        $objects = $data->getObjects();
        $this->assertEquals(1, count($objects));
        $object = $data->getObject('a');
        $this->assertTrue(isset($object['_attachments']));
        $this->assertEquals(1, count($object['_attachments']));
        $this->assertEquals(1, count($object['link-attachment']));
        $this->assertContains('test.txt', $object['link-attachment']);
        $attachment = $data->getAttachment($object['_attachments']['test.txt']['key']);
        $this->assertEquals("test\n", $attachment);

        $atc1 = Util::getTempFile();
        $fh = fopen($atc1, 'w');
        fwrite($fh, 'hhhh');
        fclose($fh);

        $info = array('tmp_name' => $atc1,
                      'name' => 'test.txt');
        $this->assertNoError($contact->addFile($info));

        $objects = $data->getObjects();
        $this->assertEquals(1, count($objects));
        $object = $data->getObject('a');
        $this->assertTrue(isset($object['_attachments']));
        $this->assertEquals(2, count($object['_attachments']));
        $this->assertEquals(2, count($object['link-attachment']));
        $this->assertContains('test[1].txt', $object['link-attachment']);
        $attachment = $data->getAttachment($object['_attachments']['test[1].txt']['key']);
        $this->assertEquals("hhhh\n", $attachment);

        $atc1 = Util::getTempFile();
        $fh = fopen($atc1, 'w');
        fwrite($fh, 'dummy');
        fclose($fh);

        $info = array('tmp_name' => $atc1,
                      'name' => 'dummy.txt');
        $this->assertNoError($contact->addFile($info));

        $objects = $data->getObjects();
        $this->assertEquals(1, count($objects));
        $object = $data->getObject('a');
        $this->assertTrue(isset($object['_attachments']));
        $this->assertEquals(3, count($object['_attachments']));
        $this->assertEquals(3, count($object['link-attachment']));
        $this->assertContains('dummy.txt', $object['link-attachment']);
        $attachment = $data->getAttachment($object['_attachments']['dummy.txt']['key']);
        $this->assertEquals("dummy\n", $attachment);

        $this->assertError($contact->deleteFile('doesnotexist.txt'), "Unable to delete VFS file.");

        $this->assertNoError($contact->deleteFile('test[1].txt'));

        $objects = $data->getObjects();
        $this->assertEquals(1, count($objects));
        $object = $data->getObject('a');
        $this->assertTrue(!isset($object['_attachments']['test[1].txt']));
        $this->assertEquals(2, count($object['_attachments']));
        $this->assertEquals(2, count($object['link-attachment']));
        $this->assertNotContains('test[1].txt', $object['link-attachment']);

        $files = $contact->listFiles();
        $this->assertNoError($files);
        
        $this->assertContains('test.txt', array_keys($files));
        $this->assertContains('dummy.txt', array_keys($files));

        $this->assertNoError($contact->deleteFiles());

        $objects = $data->getObjects();
        $this->assertEquals(1, count($objects));
        $object = $data->getObject('a');
        $this->assertTrue(!isset($object['_attachments']['test.txt']));
        $this->assertTrue(!isset($object['_attachments']));
        $this->assertTrue(!isset($object['link-attachment']));
    }
}

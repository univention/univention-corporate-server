/**
  Copyright 2021-2022 Univention GmbH

  https://www.univention.de/

  All rights reserved.

  The source code of this program is made available
  under the terms of the GNU Affero General Public License version 3
  (GNU AGPL V3) as published by the Free Software Foundation.

  Binary versions of this program provided by Univention to you as
  well as other copyrighted, protected or trademarked materials like
  Logos, graphics, fonts, specific documentations and configurations,
  cryptographic keys etc. are subject to a license agreement between
  you and Univention and not subject to the GNU AGPL V3.

  In the case you use this program under the terms of the GNU AGPL V3,
  the program is provided in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License with the Debian GNU/Linux or Univention distribution in file
  /usr/share/common-licenses/AGPL-3; if not, see
  <https://www.gnu.org/licenses/>.
* */

import { mount } from '@vue/test-utils';

import ImageUploader from '@/components/widgets/ImageUploader.vue';

const imageUploadProps = {
  extraLabel: 'Example Image',
  modelValue: '',
  forAttrOfLabel: '',
  invalidMessageId: '',
};
const $store = {
  getters: {
    'metaData/getMeta': function () {
      return {
        'umc/server/upload/max': '2048',
      };
    },
  },
};

const imageResult = 'data:image/png;base64__TEST';

let wrapper;
beforeEach(async () => {
  wrapper = await mount(ImageUploader, {
    global: {
      mocks: {
        $store,
      },
    },
    propsData: imageUploadProps,
  });
});

afterEach(() => {
  wrapper.unmount();
});

describe('ImageUploader.vue', () => {
  test('an image can be uploaded', async () => {
    const event = {
      target: {
        files: [
          {
            name: 'image.png',
            size: 5000,
            type: 'image/png',
          },
        ],
      },
    };

    // Spy on Filereader
    jest.spyOn(global, 'FileReader').mockImplementation(function () {
      this.readAsDataURL = jest.fn();
    });

    // Spy on setFile method
    const setFileSpy = jest.spyOn(wrapper.vm, 'setFile');

    let imagePreview = wrapper.find(`[data-test="imagePreview--${imageUploadProps.extraLabel}"]`);

    expect(imagePreview.exists()).toBe(false);

    // trigger upload event with test data
    wrapper.vm.onUpload(event);
    const reader = FileReader.mock.instances[0];

    expect(reader.readAsDataURL).toHaveBeenCalledWith(event.target.files[0]);
    expect(reader.onload).toStrictEqual(expect.any(Function));

    reader.onload({ target: { result: imageResult } });

    // expect update emmiter to be triggered
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');

    // expect setFile() to be called
    expect(setFileSpy).toHaveBeenCalledWith(event.target.files[0]);

    // await instance to update
    await wrapper.vm.$nextTick();

    // reassign since instance is updated.
    imagePreview = wrapper.find(`[data-test="imagePreview--${imageUploadProps.extraLabel}"]`);

    expect(imagePreview.attributes('src')).toContain(imageResult);
  });

  test('removing existing image', async () => {
    await wrapper.setProps({ modelValue: imageResult });

    // Spy on remove method
    const removeSpy = jest.spyOn(wrapper.vm, 'remove');

    let imagePreview = wrapper.find(`[data-test="imagePreview--${imageUploadProps.extraLabel}"]`);

    expect(imagePreview.exists()).toBe(true);
    expect(imagePreview.attributes('src')).toContain(imageResult);

    // trigger upload event with test data
    wrapper.vm.remove();

    // expect update emmiter to be triggered
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');

    // expect remove() to be called
    expect(removeSpy).toHaveBeenCalled();

    // await instance to update
    await wrapper.vm.$nextTick();

    // reassign since instance is updated.
    imagePreview = wrapper.find(`[data-test="imagePreview--${imageUploadProps.extraLabel}"]`);

    expect(imagePreview.exists()).toBe(false);
  });

  test('if "Select File"-Button is rendered', async () => {
    const uploadButton = await wrapper.find(`[data-test="imageUploadButton--${imageUploadProps.extraLabel}"]`);
    expect(uploadButton.text()).toBe(`Upload ${wrapper.vm.IMAGE_UPLOAD_STATE}`);
  });

  test('if "Remove"-Button is rendered and working as expected', async () => {
    const removeButton = await wrapper.find(`[data-test="imageRemoveButton--${imageUploadProps.extraLabel}"]`);

    // We expect the following text from the removeButton: "Remove "
    expect(removeButton.text()).toBe(`Remove ${imageUploadProps.extraLabel}`);
    // since there in no file uploaded, the remove button should be disabled
    expect(removeButton.attributes('disabled')).toBe('');

    await wrapper.setProps({ modelValue: imageResult });
    expect(removeButton.attributes('disabled')).toBe(undefined);
  });

  test('if IMAGE_UPLOAD_STATE is returning necessary string (A11y)', async () => {
    expect(wrapper.vm.IMAGE_UPLOAD_STATE).toBe(`${wrapper.vm.extraLabel}, ${wrapper.vm.hasImage}`);
  });

  test('if hasImage is returning the correct string', async () => {
    // hasImage should check if a value in set in modelvalue.
    // if modelValue is set hasImage should return the filename
    // If no image is set, hasImage should return 'no file selected'

    expect(wrapper.vm.hasImage).toBe('no file selected');

    await wrapper.setProps({ modelValue: imageResult });

    expect(wrapper.vm.hasImage).toBe(wrapper.vm.fileName);
  });
});

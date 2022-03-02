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
**/

import { mount } from '@vue/test-utils';

import ImageUpload from '@/components/widgets/ImageUpload';


describe('ImageUpload.vue', () => {
  test('uploading image', async () => {
    const vueProps = {
      label: 'Example Image',
      modelValue: '',
    }

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
    }
    const imageResult = 'data:image/png;base64__TEST';

    const wrapper = await mount(ImageUpload, {
      propsData: vueProps,
    });

    // Spy on Filereader
    jest.spyOn(global, 'FileReader').mockImplementation(function () {
        this.readAsDataURL = jest.fn();
    });

    // Spy on handleFile method
    const handleFileSpy = jest.spyOn(wrapper.vm, 'handleFile');
    
    let imagePreview = wrapper.find(`[data-test="imagePreview--${vueProps.label}"]`);    

    expect(imagePreview.exists()).toBe(false);

    // trigger upload event with test data
    wrapper.vm.upload(event);
    const reader = FileReader.mock.instances[0];

    expect(reader.readAsDataURL).toHaveBeenCalledWith(event.target.files[0]);
    expect(reader.onload).toStrictEqual(expect.any(Function));
    
    reader.onload({ target: { result: imageResult } });

    // expect update emmiter to be triggered
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');

    // expect handleFile() to be called
    expect(handleFileSpy).toHaveBeenCalledWith(event.target.files[0]);

    // await instance to update
    await wrapper.vm.$nextTick();

    // reassign since instance is updated. 
    imagePreview = wrapper.find(`[data-test="imagePreview--${vueProps.label}"]`);

    expect(imagePreview.attributes('src')).toContain(imageResult);
  });
  test('removing existing image', async () => {
    const imageResult = 'data:image/png;base64__TEST';

    const vueProps = {
      label: 'Example Image',
      modelValue: imageResult,
    }

    const wrapper = await mount(ImageUpload, {
      propsData: vueProps,
    });

    // Spy on remove method
    const removeSpy = jest.spyOn(wrapper.vm, 'remove');
    
    let imagePreview = wrapper.find(`[data-test="imagePreview--${vueProps.label}"]`);    

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
    imagePreview = wrapper.find(`[data-test="imagePreview--${vueProps.label}"]`);

    expect(imagePreview.exists()).toBe(false);
  });
}); 
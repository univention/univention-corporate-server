/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import Textbox from '@/components/widgets/TextBox.vue';

describe('TextBox Component', () => {
  test('user can type in input field', async () => {
    // to check focus, we need to attach to an actual document, normally we don't do this
    const div = document.createElement('div');
    div.id = 'root';
    document.body.appendChild(div);

    const wrapper = await mount(Textbox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: '',
        name: 'textBox',
        invalidMessageId: '',
      },
      attachTo: '#root',
    });

    const textBox = await wrapper.find('[data-test="text-box"]');

    // Expect input value to be empty on mount.
    expect(textBox.element.value).toBe('');

    await textBox.setValue('test input value');

    expect(textBox.element.value).toBe('test input value');

    wrapper.unmount();
  });

  test('computed property "invalud" is working', async () => {
    const wrapper = await mount(Textbox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: '',
        invalidMessageId: '',
        name: 'textBox',
      },
    });

    // Expect Aria-Invalid to be set correctly
    expect(wrapper.vm.invalid).toBe(false);
    await wrapper.setProps({ invalidMessage: 'Invalid Message' });
    expect(wrapper.vm.invalid).toBe(true);
  });

  test('input field has id attribute with value (needed for A11y reasons)', async () => {
    const wrapper = await mount(Textbox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: 'testString',
        name: 'textBox',
        invalidMessageId: '',
      },
    });
    const textBox = await wrapper.find('[data-test="text-box"]');
    expect(textBox.attributes('id')).toBe('testString');
  });
});

/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import NumberSpinner from '@/components/widgets/NumberSpinner.vue';

describe('NumberSpinner Component', () => {
  test('user can type in input field', async () => {
    // to check focus, we need to attach to an actual document, normally we don't do this
    const div = document.createElement('div');
    div.id = 'root';
    document.body.appendChild(div);

    const wrapper = await mount(NumberSpinner, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: '',
        name: 'numberSpinner',
        invalidMessageId: '',
      },
      attachTo: '#root',
    });

    const numberSpinner = await wrapper.find('[data-test="number-spinner"]');

    // Expect input value to be empty on mount.
    expect(numberSpinner.element.value).toBe('');

    await numberSpinner.setValue('test input value');

    expect(numberSpinner.element.value).not.toBe('test input value');
    await numberSpinner.setValue(12);
    expect(numberSpinner.element.value).toBe('12');

    wrapper.unmount();
  });

  test('computed property "invalud" is working', async () => {
    const wrapper = await mount(NumberSpinner, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: '',
        invalidMessageId: '',
        name: 'numberSpinner',
      },
    });

    // Expect Aria-Invalid to be set correctly
    expect(wrapper.vm.invalid).toBe(false);
    await wrapper.setProps({ invalidMessage: 'Invalid Message' });
    expect(wrapper.vm.invalid).toBe(true);
  });

  test('input field has id attribute with value (needed for A11y reasons)', async () => {
    const wrapper = await mount(NumberSpinner, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: 'testString',
        name: 'numberSpinner',
        invalidMessageId: '',
      },
    });
    const numberSpinner = await wrapper.find('[data-test="number-spinner"]');
    expect(numberSpinner.attributes('id')).toBe('testString');
  });
});

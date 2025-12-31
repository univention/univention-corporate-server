/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import DateBox from '@/components/widgets/DateBox.vue';

describe('DateBox Component', () => {
  test('date input is working as expected', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        name: 'datebox',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });

    const dateBox = await wrapper.find('[data-test="date-box"]');

    // Expect input value to be empty on mount.
    expect(dateBox.element.value).toBe('');
    await dateBox.setValue('2017-06-01');
    expect(dateBox.element.value).toBe('2017-06-01');

    // TODO check if wrong date input return false eg: 30.02.1993

    await dateBox.setValue('text string');
    expect(dateBox.element.value).not.toBe('text string');
    expect(dateBox.element.value).toBe('');

    wrapper.unmount();
  });

  test('this.invalid should return correct boolean', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        name: 'datebox',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });

    // this.invalid returns true if this.invalidMessage has a non-empty string
    expect(wrapper.vm.invalid).toBe(false);
    await wrapper.setProps({ invalidMessage: 'Invalid Message' });
    expect(wrapper.vm.invalid).toBe(true);

    // TODO select element should have aria-invalid true or false
    // depending on this.invalid
  });

  test('it is an input type=date', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        name: 'datebox',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });
    const dateBox = await wrapper.find('[data-test="date-box"]');
    expect(dateBox.attributes('type')).toBe('date');
  });

  test('it has the attribute id with a value from Prop //A11y', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: 'testString',
        name: 'datebox',
        invalidMessageId: '',
      },
    });
    const dateBox = await wrapper.find('[data-test="date-box"]');
    expect(dateBox.attributes('id')).toBe('testString');
  });
});

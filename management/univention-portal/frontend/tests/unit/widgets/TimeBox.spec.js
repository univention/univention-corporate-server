/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import TimeBox from '@/components/widgets/TimeBox.vue';

describe('TimeBox Component', () => {
  test('user can type in input field', async () => {
    // to check focus, we need to attach to an actual document, normally we don't do this
    const div = document.createElement('div');
    div.id = 'root';
    document.body.appendChild(div);

    const wrapper = await mount(TimeBox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: '',
        name: 'timeBox',
        invalidMessageId: '',
      },
      attachTo: '#root',
    });

    const timeBox = await wrapper.find('[data-test="time-box"]');

    // Expect input value to be empty on mount.
    expect(timeBox.element.value).toBe('');

    await timeBox.setValue('test input value');
    expect(timeBox.element.value).toBe('');

    await timeBox.setValue('13:00');
    expect(timeBox.element.value).toBe('13:00');

    wrapper.unmount();
  });

  test('computed property "invalid" is working', async () => {
    const wrapper = await mount(TimeBox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: '',
        invalidMessageId: '',
        name: 'timeBox',
      },
    });

    // Expect Aria-Invalid to be set correctly
    expect(wrapper.vm.invalid).toBe(false);
    await wrapper.setProps({ invalidMessage: 'Invalid Message' });
    expect(wrapper.vm.invalid).toBe(true);
  });

  test('input field has id attribute with value (needed for A11y reasons)', async () => {
    const wrapper = await mount(TimeBox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: 'testString',
        name: 'timeBox',
        invalidMessageId: '',
      },
    });
    const timeBox = await wrapper.find('[data-test="time-box"]');
    expect(timeBox.attributes('id')).toBe('testString');
  });

  test('Can set seconds, also if steps prop has been set.', async () => {
    const wrapper = await mount(TimeBox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: 'testString',
        name: 'timeBox',
        invalidMessageId: '',
        steps: 5,
      },
    });
    const timeBox = await wrapper.find('[data-test="time-box"]');
    await timeBox.setValue('13:00:05');
    expect(timeBox.element.value).toBe('13:00:05');
  });
});

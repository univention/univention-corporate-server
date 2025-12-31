/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import RadioBox from '@/components/widgets/RadioBox.vue';

const radioBoxName = 'radio-selection';

const radioElementProps = {
  modelValue: '',
  name: radioBoxName,
  options: [
    {
      id: 'yes',
      label: 'Yes',
    },
    {
      id: 'no',
      label: 'No',
    },
  ],
};

describe('RadioBox Component', () => {
  test('input setting', async () => {
    const wrapper = await mount(RadioBox, {
      propsData: radioElementProps,
    });

    const radioBoxInputYes = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);

    const radioBoxInputNo = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[1].id}"]`);

    // Expect after mounting that none of both radio options is checked
    expect(radioBoxInputYes.element.checked).toBeFalsy();
    expect(radioBoxInputNo.element.checked).toBeFalsy();
    expect(wrapper.vm.modelValue).toBe('');

    await radioBoxInputYes.trigger('click');

    expect(radioBoxInputYes.element.checked).toBeTruthy();
    expect(radioBoxInputNo.element.checked).toBeFalsy();
    expect(wrapper.vm.modelValue).toBe(radioElementProps.options[0].id);

    wrapper.unmount();
  });

  test('click on label should set modelValue', async () => {
    const wrapper = await mount(RadioBox, {
      propsData: radioElementProps,
    });

    const radioBoxLabelYes = await wrapper.find(`[for="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);
    const radioBoxInputYes = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);

    expect(radioBoxInputYes.element.checked).toBeFalsy();

    await radioBoxLabelYes.trigger('click');

    expect(radioBoxInputYes.element.checked).toBeTruthy();
  });

  test('Check Focus', async () => {
    // to check focus, we need to attach to an actual document, normally we don't do this
    const div = document.createElement('div');
    div.id = 'root';
    document.body.appendChild(div);

    const wrapper = await mount(RadioBox, {
      propsData: radioElementProps,
      attachTo: '#root',
    });
    const radioBoxInputYes = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);

    expect(radioBoxInputYes.element).not.toBe(document.activeElement);

    await radioBoxInputYes.setChecked();

    // TODO Fix test for focus. For some reason it is not working
    // expect(radioBoxInputYes.element).toBe(document.activeElement);
  });
});

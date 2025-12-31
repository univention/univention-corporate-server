/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import FormElement from '@/components/forms/FormElement.vue';
import { mount } from '@vue/test-utils';

describe('FormElement Component', () => {
  test('Can render a widget component', async () => {
    const widget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: '',
      required: true,
    };

    const widgetValue = '';

    const wrapper = await mount(FormElement, {
      propsData: {
        widget,
        modelValue: widgetValue,
      },
    });
    const expectedComponent = widget;

    delete expectedComponent.type;
    delete expectedComponent.label;
    delete expectedComponent.validators;

    // Based by the values in the widget object we have following expectacions
    expect(wrapper.vm.widget).toStrictEqual(widget);
    expect(wrapper.vm.modelValue).toBe('');
    expect(wrapper.vm.component).toStrictEqual(expectedComponent);
  });

  test('computed property invalid is returning expected boolean', async () => {
    // this.invalid should return false if widget.invalidMessage === ''
    // this.invalid should return true if widget.invalidMessage has actually Text in it.
    const widget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: '',
      required: true,
    };

    const widgetValue = '';

    const wrapper = await mount(FormElement, {
      propsData: {
        widget,
        modelValue: widgetValue,
      },
    });

    expect(wrapper.vm.invalid).toBe(false);

    // By setting a message in invalidMessage wrapper.vm.invalid should be true.
    const updatedWidget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: 'Test String.',
      required: true,
    };

    await wrapper.setProps({ widget: updatedWidget });
    expect(wrapper.vm.invalid).toBe(true);
  });

  test('invalidMessage is working as expected', async () => {
    const widget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: 'This is an invalid Message',
      required: true,
    };

    const widgetValue = '';

    const wrapper = await mount(FormElement, {
      propsData: {
        widget,
        modelValue: widgetValue,
      },
    });

    expect(wrapper.vm.invalidMessage).toBe('This is an invalid Message');

    const updatedWidget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: '',
      required: true,
    };
    await wrapper.setProps({ widget: updatedWidget });
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.invalidMessage).toBe('');
  });

  test('component has .form-element--invalid class when this.invalid === true', async () => {
    const widget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: '',
      required: true,
    };

    const widgetValue = '';

    const wrapper = await mount(FormElement, {
      propsData: {
        widget,
        modelValue: widgetValue,
      },
    });

    // now we expect, that the element has no invalis class,
    //  since its value it not invalid

    expect(wrapper.classes('form-element--invalid')).toBe(false);

    // When we update the component with an invalid Message,
    // we expect that the formelement has now the invalid class
    const updatedWidget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: 'The value is invalid',
      required: true,
    };
    await wrapper.setProps({ widget: updatedWidget });
    await wrapper.vm.$nextTick();
    expect(wrapper.classes('form-element--invalid')).toBe(true);
  });
  test('computed prop for label and input id element exists (A11y)', async () => {
    const widget = {
      type: 'TextBox',
      name: 'userInput',
      label: 'userInput',
      invalidMessage: '',
      required: true,
    };

    const widgetValue = '';

    const wrapper = await mount(FormElement, {
      propsData: {
        widget,
        modelValue: widgetValue,
      },
    });

    const label = await wrapper.find('[data-test="form-element-label"]');
    const inputComponent = await wrapper.find('[data-test="form-element-component"]');

    const forAttrOfLabel = wrapper.vm.forAttrOfLabel;

    expect(label.attributes('for')).toBe(forAttrOfLabel);
    expect(inputComponent.attributes('id')).toBe(forAttrOfLabel);
  });

  test.todo('this.correct label is working depending on if input is in multiinput');
});

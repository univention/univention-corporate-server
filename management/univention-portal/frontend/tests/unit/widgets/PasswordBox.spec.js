/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import PasswordBox from '@/components/widgets/PasswordBox.vue';
import ToggleButton from '@/components/widgets/ToggleButton.vue';
import Vuex from 'vuex';
import activity from '@/store/modules/activity';

const store = new Vuex.Store({
  modules: {
    activity: {
      getters: activity.getters,
      namespaced: true,
    },
  },
});

describe('PasswordBox Component', () => {
  test('input value', async () => {
    // to check focus, we need to attach to an actual document, normally we don't do this
    const div = document.createElement('div');
    div.id = 'root';
    document.body.appendChild(div);

    const wrapper = await mount(PasswordBox, {
      propsData: {
        modelValue: '',
        name: 'password',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
      attachTo: '#root',
    });

    const passwordBox = await wrapper.find('[data-test="password-box"]');

    // Expect input value to be empty on mount.
    expect(passwordBox.element.value).toBe('');

    await passwordBox.setValue('test input value');

    expect(passwordBox.element.value).toBe('test input value');

    wrapper.unmount();
  });

  test('computed property', async () => {
    const wrapper = await mount(PasswordBox, {
      propsData: {
        modelValue: '',
        name: 'password',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });

    // Expect Aria-Invalid to be set correctly
    expect(wrapper.vm.invalid).toBe(false);
    await wrapper.setProps({ invalidMessage: 'Invalid Message' });
    expect(wrapper.vm.invalid).toBe(true);
  });

  test('its actually a password input field', async () => {
    const wrapper = await mount(PasswordBox, {
      propsData: {
        modelValue: '',
        name: 'password',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });
    const passwordBox = await wrapper.find('[data-test="password-box"]');

    expect(passwordBox.attributes('type')).toBe('password');
  });

  test('show/hide password icon button', async () => {
    const wrapper = await mount(PasswordBox, {
      propsData: {
        modelValue: '',
        name: 'password',
        forAttrOfLabel: '',
        invalidMessageId: '',
        canShowPassword: true,
      },
      children: [ToggleButton],
      global: {
        plugins: [store],
      },
    });

    const passwordBox = await wrapper.find('[data-test="password-box"]');
    const passwordBoxButton = await wrapper.find('[data-test="password-box-icon"]');

    expect(passwordBoxButton.attributes('aria-label')).toBe('Show password');
    expect(passwordBox.attributes('type')).toBe('password');

    await passwordBoxButton.trigger('click');

    expect(passwordBoxButton.attributes('aria-label')).toBe('Hide password');
    expect(passwordBox.attributes('type')).toBe('text');
  });
});

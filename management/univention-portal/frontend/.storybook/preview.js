/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import Vuex from 'vuex';
import { store } from '../src/store';
import { app } from '@storybook/vue3'
import Portal from '../src/views/Portal';
import VueDOMPurifyHTML from 'vue-dompurify-html';
import localize from '@/plugins/localize';


app
  .use(store)
  .use(localize)
  .use(VueDOMPurifyHTML, {
    hooks: {
      afterSanitizeAttributes: (currentNode) => {
        // Do something with the node
        // set all elements owning target to target=_blank
        if ('target' in currentNode) {
          currentNode.setAttribute('target', '_blank');
          currentNode.setAttribute('rel', 'noopener');
        }
      },
    },
  });

app.component('portal', Portal);

const viewportMeta = document.createElement('meta');
viewportMeta.name = "viewport";
viewportMeta.content = "width=device-width,initial-scale=1";

const lightColor = '#F8F8F8';
const darkColor = '#333333';

export const parameters = {
  actions: { argTypesRegex: "^on[A-Z].*" },
  layout: 'centered',
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
  backgrounds: {
    default: 'light',
    values: [
      {
        name: 'light',
        value: lightColor,
      },
      {
        name: 'dark',
        value: darkColor,
      },
    ],
  },
  options: {
    storySort: {
      order: ['Introduction', ['Portal'], 'Layout', 'Globals', 'Widgets'],
    },
  },
}


// look https://github.com/storybookjs/storybook/discussions/17652
import addons from "@storybook/addons";
import { GLOBALS_UPDATED } from "@storybook/core-events";
import { useArgs } from '@storybook/client-api';

function changeCSS(themeColor) {
  const themeCss = document.createElement('link');
  themeCss.id = 'current-theme-css';
  themeCss.rel = 'stylesheet';

  if (themeColor === lightColor) {
    themeCss.href = `data/light.css`;
  }

  if (themeColor === darkColor) {
    themeCss.href = `data/dark.css`;
  }

  document.head.appendChild(themeCss);
}

const channel = addons.getChannel();
channel.on(GLOBALS_UPDATED, ({globals}) => {
  if (globals.backgrounds && globals.backgrounds.value) {
    const links = document.getElementById('current-theme-css');
    if (links) {
      links.remove();
    }

    changeCSS(globals.backgrounds.value);
  }
});

// set global css
import '!style-loader!css-loader!stylus-loader!../src/assets/styles/style.styl';
// set default theme
changeCSS(lightColor);

// set default container && add updateArgs to StoryContext
export const decorators = [(story, context) => {
  const [_, updateArgs] = useArgs();
  return story({...context, updateArgs})
}, () => ({template: '<story class="story-container" />'})];

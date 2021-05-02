const path = require('path');

const vueConfig = {
  filenameHashing: false,
  pwa: {
    name: 'Univention Portal',
  },
  chainWebpack: (config) => {
    config
      .plugin('html')
      .tap((args) => {
        args[0].title = 'Univention Portal';
        return args;
      });
  },
  css: {
    sourceMap: true,
    loaderOptions: {
      stylus: {
        import: [
          path.resolve(__dirname, 'src/assets/styles/_vars.styl'),
          path.resolve(__dirname, 'src/assets/styles/_variables.styl'),
          path.resolve(__dirname, 'src/assets/styles/_base.styl'),
        ],
      },
    },
  },
  publicPath: './',
};

const existingConfigureWebpack = vueConfig.configureWebpack;

vueConfig.configureWebpack = (config) => {
  if (existingConfigureWebpack) {
    existingConfigureWebpack(config);
  }

  config.module.rules.push({
    test: /\.ya?ml$/,
    loader: 'json-loader!yaml-loader',
  });
};

const existingChainWebpack = vueConfig.chainWebpack;

vueConfig.chainWebpack = (config) => {
  if (existingChainWebpack) {
    existingChainWebpack(config);
  }

  // Also look at
  //   jest.config.js
  //   tsconfig.json
  config.resolve.alias
    // components
    .set('components', path.resolve(__dirname, 'src/components'))
    .set('globals', path.resolve(__dirname, 'src/components/globals'))

    // other stuff
    .set('assets', path.resolve(__dirname, 'src/assets'))
    .set('mixins', path.resolve(__dirname, 'src/mixins'))
    .set('views', path.resolve(__dirname, 'src/views'));

  // TODO: In case that the paths will not be resolved in production we might have to install 'module-alias': https://medium.com/@caludio/how-to-use-module-path-aliases-in-visual-studio-typescript-and-javascript-e7851df8eeaa
};

module.exports = vueConfig;

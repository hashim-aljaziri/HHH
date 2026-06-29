const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const isDevelopment = process.env.NODE_ENV !== 'production';

// Simpler webpack config that works with minimal setup
module.exports = {
  mode: isDevelopment ? 'development' : 'production',
  entry: {
    main: './static/css/main.css',
  },
  output: {
    path: path.resolve(__dirname, 'static/dist'),
    filename: '[name].js',
    assetModuleFilename: '[name][ext]',
    clean: true,
  },
  devtool: isDevelopment ? 'source-map' : false,
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
            },
          },
          'postcss-loader',
        ],
      },
      {
        test: /\.(png|jpg|jpeg|gif|svg)$/,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 8 * 1024,
          },
        },
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/,
        type: 'asset/resource',
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: '[name].[contenthash].css',
    }),
  ],
  optimization: {
    minimize: !isDevelopment,
    nodeEnv: process.env.NODE_ENV,
  },
  performance: {
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
  },
  watchOptions: {
    ignored: /node_modules/,
    poll: 1000,
  },
};

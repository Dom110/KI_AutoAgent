/**
 * Webpack configuration for VS Code Extension bundling
 * This bundles the extension into a single file for better performance
 */
const path = require('path');

module.exports = {
    target: 'node', // VS Code extensions run in a Node.js-context
    mode: 'none', // this leaves the source code as close as possible to the original (when packaging we set this to 'production')

    entry: './src/extension.ts', // the entry point of this extension
    output: {
        // the bundle is stored in the 'dist' folder (check package.json), 📖 -> https://webpack.js.org/configuration/output/
        path: path.resolve(__dirname, 'dist'),
        filename: 'extension.js',
        libraryTarget: 'commonjs2'
    },
    externals: {
        vscode: 'commonjs vscode', // the vscode-module is created on-the-fly and must be excluded. Add other modules that cannot be webpack'ed, 📖 -> https://webpack.js.org/configuration/externals/
        ws: 'commonjs ws' // WebSocket library should not be bundled
        // modules added here also need to be added in the .vscodeignore file
    },
    externalsPresets: { node: true },
    resolve: {
        // support reading TypeScript and JavaScript files, 📖 -> https://github.com/TypeStrong/ts-loader
        extensions: ['.ts', '.js'],
        fallback: {
            "bufferutil": false,
            "utf-8-validate": false
        },
        alias: {
            'debug': path.resolve(__dirname, 'node_modules/follow-redirects/debug.js')
        }
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                exclude: /node_modules/,
                use: [
                    {
                        loader: 'ts-loader'
                    }
                ]
            }
        ]
    },
    devtool: 'nosources-source-map',
    infrastructureLogging: {
        level: "log", // enables logging required for problem matchers
    },
};
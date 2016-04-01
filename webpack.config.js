var path = require("path");
var webpack = require("webpack");

module.exports = {
    resolve: {
        root: [path.join(__dirname, "app/bower_components")]
    },
    plugins: [
        new webpack.ResolverPlugin(
            new webpack.ResolverPlugin.DirectoryDescriptionFilePlugin("bower.json", ["main"])
        )
    ],
    entry: {
        plugin: "./app/static/js/audience-plugin.js",
        widget_seats: "./app/static/js/widget_seats.js"
    },
    output: {
        path: __dirname + "/app/static/js/bundle",
        filename: "[name].js"
    },
    module: {
        loaders: [
            {
                test: /\.js$/,
                loader: "babel-loader",
                query: {
                    presets: ["es2015"]
                }
            }
        ]
    },
    devtool: "source-map",
    debug: true
};

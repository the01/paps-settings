"use strict";


(function () {
    "use strict";

    var Library = function () {
        var self = this;
        this.version = "0.1.0";
        this.active_plugin = null;
        this.pluginLoaded = null;

        this.PluginListViewModel = function (mainuri) {
            var self = this;
            this.uri = mainuri;
            this.plugins = ko.observableArray();

            this.load_list = function () {
                var list_plugins = self.plugins;
                AUDUtils.ajaxRest(self.uri, "GET", undefined, false).then(function (data) {
                    for (var plugin in data.plugins) {
                        if (data.plugins.hasOwnProperty(plugin)) {
                            plugin = data.plugins[plugin];
                            list_plugins.push(plugin);
                        }
                    }
                    setTimeout(AUDPlugin.plugin_autoselect, 0);
                    
                }, function (jqXHR, textStatus, errorThrown) {
                    console.error("Failed to load " + self.uri + " (Error: " + jqXHR + ")");
                    console.error(textStatus);
                    console.error(errorThrown);
                });
            };

            this.link_click = function (plugin, event) {
                // console.info("Clicked");
                var a = event.target;
                AUDPlugin.plugin_activate(plugin, a);
            };

            this.load_list();
        };

        /**
         * Register the active plugin object
         *
         * @param {object} plugin Plugin to register (must have a unique name!)
         */
        this.plugin_register = function (plugin) {
            console.debug("Registering " + plugin.name);
            if (AUDPlugin.active_plugin != null && AUDPlugin.active_plugin.name == plugin.name) {
                console.info("Plugin " + plugin.name + " already active");
            }
            else {
                console.info("Plugin " + plugin.name + " registered");
                AUDPlugin.active_plugin = plugin;
            }
            // Got plugins -> resolve promise
            AUDPlugin.pluginLoaded.resolve();
        };

        this.plugin_load = function (plugin_uri) {
            AUDUtils.ajaxRest(plugin_uri, "GET", undefined, false).then(function (data) {
                AUDPlugin.pluginLoaded = $.Deferred();
                var plugin = data.plugin;

                if (AUDPlugin.active_plugin != null && typeof AUDPlugin.active_plugin.exit == typeof Function) {
                    AUDPlugin.active_plugin.exit(AUDPlugin.active_plugin.name);
                    AUDPlugin.active_plugin = null;
                }

                var p_head = $("#plugin_name");
                var p_art = $("#plugin_description");
                var p_widget = $("#plugin_widget");
                p_head.text(plugin.name);

                if (plugin.hasOwnProperty("description")) {
                    p_art.text(plugin.description);
                }
                else {
                    p_art.text("");
                }

                // clear old
                $(".plugin_resource").remove();
                p_widget.text("No resources provided by plugin");

                if (plugin.hasOwnProperty("resources")) {
                    // load css first, then everything else and finally js
                    var resources = [];
                    var js = [], css = [], html = [];
                    var index = -1;
                    var key, uri;

                    // Sort resources
                    for (key in plugin.resources) {
                        if (!plugin.resources.hasOwnProperty(key)) {
                            // skip inherited
                            continue;
                        }
                        var ext = key.substr((key.lastIndexOf(".") + 1));

                        if (ext == "css") {
                            resources.splice(0, 0, key);
                            index++;
                            css.push(key);
                        }
                        else if (ext == "js") {
                            resources.push(key);
                            js.push(key);
                        }
                        else {
                            resources.splice(index, 0, key);
                            html.push(key);
                        }
                    }

                    var promiseCSS = [];
                    var promiseHTML = [];
                    var promiseJS = [];
                    
                    // Load css
                    for (index in css) {
                        key = css[index];
                        uri = plugin.resources[key];
                        promiseCSS.push(AUDUtils.resource_load(key, uri, p_widget, "plugin_resource"));
                    }

                    Promise.all(promiseCSS).then(function () {
                        console.info("CSS loaded");
                        // CSS loaded
                        for (index in html) {
                            key = html[index];
                            uri = plugin.resources[key];
                            promiseHTML.push(AUDUtils.resource_load(key, uri, p_widget, "plugin_resource"));
                        }
                        
                        Promise.all(promiseHTML).then(function () {
                            console.info("HTML loaded");
                            // HTML loaded
                            for (index in js) {
                                key = js[index];
                                uri = plugin.resources[key];
                                promiseJS.push(AUDUtils.resource_load(key, uri, p_widget, "plugin_resource"));
                            }
                            
                            promiseJS.push(AUDPlugin.pluginLoaded);
                            Promise.all(promiseJS).then(function () {
                                var retries = 3;

                                function activatePlugin () {
                                    retries -= 1;

                                    if (AUDPlugin.active_plugin == null || AUDPlugin.active_plugin.name != plugin.key) {
                                        // Plugin not yet active
                                        if (retries <= 0) {
                                            console.error("Plugin not registered");
                                        } else {
                                            setTimeout(activatePlugin, 3);
                                        }
                                    } else {
                                        // Assume js is setup
                                        if ($.type(AUDPlugin.active_plugin.enter) === "function") {
                                            // trigger delayed or it wont render
                                            AUDPlugin.active_plugin.enter(plugin.key, plugin.uri, plugin.data);
                                        }
                                    }
                                }
                                console.info("JS loaded");
                                // JS loaded
                                activatePlugin();
                            });
                        });
                    });
                }
            }, function (jqXHR, textStatus, errorThrown) {
                console.error("Failed to load " + plugin_uri + " (Error: " + jqXHR + ")");
            });
        };

        /**
         * Select and activate first plugin
         */
        this.plugin_autoselect = function () {
            var links = $("#plugin_list_container a");
            //console.debug(AUDPlugin.active_plugin);
            //console.debug(links.length);
            //console.debug(links);
            if (links.length > 0 && links[0]["href"] != "" && AUDPlugin.active_plugin == null) {
                // Only change if we have plugins and there is no active plugins
                links[0].click();
            }
        };

        this.plugin_activate = function (data, a) {
            var container_link = $("#plugin_list_container a");
            //var detail = $(this).next(".post-detail");
            container_link.removeClass("active");
            $(a).addClass("active");
            AUDPlugin.plugin_load(data["uri"]);
        };

        /**
         * Async send data to server
         *
         * @param {String}  uri     Server adress to send to
         * @param {Object}  data    Data to send
         * @return {Promise} Return transmit promise
         */
        this.data_set = function (uri, data) {
            var transmit = {
                "data": data
            };
            return AUDUtils.ajaxRest(uri, "POST", transmit, true).then(function (data) {
                // Post worked
            }, function(jqXHR, textStatus, errorThrown) {
                console.error("Failed to load " + uri + " (Error: " + jqXHR + ")");
            });
        };

        /**
         * Function to send data changes to active plugin
         *
         * @param {String} widget    Widget name updating
         * @param {object} data      Changed data
         * @returns {object} Return value of active plugin call
         */
        this.widgetDataSet = function (widget, data) {
            if (!self.active_plugin) {
                console.error("No active plugin found");
                return;
            }

            if (typeof self.active_plugin.widgetDataSet != typeof Function) {
                console.error("Active plugin does not support widgetDataSet");
                return;
            }

            return self.active_plugin.widgetDataSet(widget, data);
        };

        // Return as object
        return this;
    };

    if (!window.AUDPlugin) {
        window.AUDPlugin = new Library();
    }
})();


/**
 * Init a AUDPlugin lib
 */
function init () {
    console.info("Initing AUDPlugin");
    var plvm = new AUDPlugin.PluginListViewModel($("#plugin_list_container").attr("data-aud-api-plugin"));
    var links = $("#plugin_list_container a");
    
    links.click(function (e) {
        // stop link
        e.preventDefault();
        //var detail = $(this).next('.post-detail');
        links.removeClass("active");
        var link = $(this);
        var href = link.attr("href");
        link.addClass("active");
        AUDPlugin.plugin_load(href);
    });
    
    ko.applyBindings(plvm, $("#plugin_list_container")[0]);
}


$(document).ready(function () {
    // init();
});

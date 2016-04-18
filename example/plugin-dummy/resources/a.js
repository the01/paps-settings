/**
 * Created by flo on 28.06.15.
 */


(function () {
    "use strict";

    var Library = function () {
        var self = this;
        var ego = this;
        this.version = "0.1.0";
        this.name = "DummyPlugin";
        this.svm = null;
        this.uri = null;

        this.SettingsViewModel = function (data) {
            var self = this;
            this.var1 = ko.observable(data.var1);
            this.var2 = ko.observable(data.var2);
            this.groups = null;

            this.on_submit = function (formElement) {
                console.debug("Submitted: " + formElement);
                // console.log(self.var1());
                // console.log(self.var2());
                data = {
                    "var1": self.var1(),
                    "var2": self.var2()
                };

                if (self.groups) {
                    data["groups"] = self.groups;
                }
                console.debug(data);
                AUDPlugin.data_set(ego.uri, data);
            };
        };

        this.enter = function (plugin_name, uri, data) {
            console.info(plugin_name + " is ready");
            // Set api url
            self.uri = uri;
            if (self.svm == null) {
                // create model
                self.svm = new self.SettingsViewModel(data);
                ko.applyBindings(self.svm, $("#plugin_widget")[0]);
            }
            else {
                // update model
                self.svm.var1(data.var1);
                self.svm.var2(data.var2);
            }
            // Set seats
            AUDWidget_seats.load(data);
        };


        this.exit = function (plugin_name) {
            console.info(plugin_name + " is being unloaded");
            ko.cleanNode($("#plugin_widget")[0]);
            self.svm = null;
            self.uri = null;
            delete window.AUDPlugin_dummy;
        };

        this.widgetDataSet = function (widget, data) {
            console.info(widget + " is updating data");
            //console.debug(data);
            if (widget == "AUDWidget_seats") {
                if (self.svm) {
                    self.svm.groups = data.groups;
                }
            }
            else {
                console.warn("Unsupported widget " + widget);
                console.debug(data);
            }
        };
    };

    if (!window.AUDPlugin_dummy) {
        window.AUDPlugin_dummy = new Library();
    }

    // Plugin loaded -> register with AUDPlugin
    AUDPlugin.plugin_register(AUDPlugin_dummy);
})();

"use strict";

(function () {
    "use strict";
    
    var Library = function () {
        var self = this;
        var ego = this;
        self.version = "0.1.0";
        this.glvm = null;
        this.loading = false;

        this.Person = function (id, sitting) {
            var self = this;
            this.fake = false;
            this.name = id;
            self.sitting = sitting;

            if (self.sitting === undefined) {
                self.sitting = false;
            }
            self.sitting = ko.observable(self.sitting);
            this.format = ko.computed(function () {
                return "Person(" + self.name + ", " + self.sitting() + ")";
            });
        };

        this.GroupViewModel = function (name, id) {
            var self = this;
            if (id == undefined) {
                id = 0;
            }
            this.id = id;
            this.original = {};
            this.name = ko.observable(name);
            this.editing = ko.observable(false);
            this.people = ko.observableArray();

            // Behaviors
            this.show_input = ko.computed(function () {
                return self.editing() || (self.name() == "");
            });

            this.show_input.subscribe(function (val) {
                if (!val) {
                    // No longer editing
                    // New name -> tell plugin
                    ego.pluginDataUpdate();
                }
            });

            this.edit = function () {
                this.editing(true)
            };

            this.onAdd = ko.pureComputed({
                read: function () {
                    return ""
                },
                write: function (/**Event*/evt) {
                    console.debug("GVM." + self.id + ":Add");
                    //console.debug(self.people()[0]);
                    AUDWidget_seats.clear_fake(self, 0);
                    // Add person -> tell plugin
                    // ego.pluginDataUpdate();
                    // Remove happens after add -> tell plugin via onRemove
                    return true;
                },
                owner: self
            });

            this.onRemove = ko.pureComputed({
                read: function () {
                    return ""
                },
                write: function (/**Event*/evt) {
                    console.debug("GVM." + self.id + ":Remove");
                    //console.debug(self.people());
                    // Person not yet removed from list, so length of 1 means empty
                    if (self.people().length == 1) {
                        self.people.push({
                            fake: true,
                            format: function () {
                                return "Empty";
                            }
                        });
                    }
                    // Remove person -> tell plugin
                    setTimeout(function () {
                        ego.pluginDataUpdate();
                    }, 0);
                },
                owner: self
            });
        };

        this.GroupListViewModel = function () {
            var self = this;
            this.groups = ko.observableArray();
            // Not yet placed people
            this.nypp = new AUDWidget_seats.GroupViewModel("Not yet placed people", 0);
            // Title not editable for this model
            this.nypp.edit = function () {};

            this.group_form_add = function (form) {
                var inp = $(form).find("#seats_list_group_add_name");
                this.group_add(inp.val());
                inp.val("");
            };

            this.group_add = function (name, id) {
                if (name == "") {
                    return;
                }
                var i;
                var newId = id;

                // If no id -> find new unique group id
                if (newId === undefined) {
                    newId = 1;

                    for (i = 0; i < self.groups().length; i++) {
                        console.debug(self.groups()[i]);
                        if (self.groups()[i].id == newId) {
                            i = 0;
                            newId++;
                        }
                    }
                }

                var group = new AUDWidget_seats.GroupViewModel(name, newId);
                // Group is empty for now -> placeholder
                group.people.push({
                    fake: true,
                    format: function () {
                        return "Empty";
                    }
                });
                self.groups.push(group);
                // New group -> tell plugin
                ego.pluginDataUpdate();
                return group;
            };

            this.group_remove = function (group) {
                // console.log("Delete " + group.people().length);
                // Move people to nypp
                while (group.people().length > 0) {
                    self.nypp.people.push(group.people.pop());
                }
                AUDWidget_seats.clear_fake(self.nypp, 1);
                self.groups.remove(group);
                // Delete group -> tell plugin
                ego.pluginDataUpdate();
            }
        };

        this.clear_fake = function (group, number) {
            if (group.people().length > number) {
                // have to remove the old element delayed or both get deleted
                setTimeout(function () {
                    // console.log("really remove ;)");
                    group.people.remove(function (item) {
                        return item.fake;
                    });
                }, 50);
            }
        };

        this.loadPeople = function (group, personList) {
            var i;
            // Clear existing
            //console.debug(personList);
            group.people.removeAll();
            // Add people
            for (i=0; i < personList.length; i++) {
                group.people.push(
                    new AUDWidget_seats.Person(personList[i].id, personList[i].sitting)
                );
            }

            // Make sure a fake empty placeholder is shown if no people
            if (group.people().length < 1) {
                group.people.push({
                    fake: true,
                    format: function () {
                        return "Empty";
                    }
                });
            }
        };

        this.load = function (data) {
            //console.info("Loading Seats");
            // Clear old groups
            self.glvm.groups.removeAll();
            self.loading = true;

            var groups = new Object(data.groups);
            if ($.isEmptyObject(groups)) {
                console.error("No groups set");
                return;
            }
            var i;
            for (i=0; i < groups.length; i++) {
                var group = groups[i];
                if (group.id === 0) {
                    // Got nypp
                    var gvm = self.glvm.nypp;
                    gvm.name(group.name);
                    gvm.original = group;
                    self.loadPeople(gvm, group.people);
                }
                else {
                    // Got new group
                    var gvm = self.glvm.group_add(group.name, group.id);
                    gvm.original = group;
                    self.loadPeople(gvm, group.people);
                }
            }
            self.loading = false;
            self.pluginDataUpdate();
        };

        this.pluginDataUpdate = function () {
            console.debug("UPDATE")
            function people2object (people) {
                var res = [];

                for (var i=0; i < people.length; i++) {
                    var person = people[i];
                    if (person.fake) {
                        // Not real person -> skip
                        continue;
                    }
                    res.push({
                        "id": person.name
                    });
                }
                return res;
            }

            function group2object (group) {
                var res = new Object(group.original);
                res.id = group.id;
                res.name = group.name();
                res.people = people2object(group.people());
                return res;
            }

            if (self.loading) {
                return;
            }
            var groups = [];
            var i;

            if (self.glvm) {
                if (self.glvm.nypp) {
                    groups.push(group2object(self.glvm.nypp));
                }
                if (self.glvm.groups && self.glvm.groups()) {
                    for (i=0; i < self.glvm.groups().length; i++) {
                        groups.push(group2object(self.glvm.groups()[i]));
                    }
                }
            }
            return AUDPlugin.widgetDataSet("AUDWidget_seats", {"groups": groups});
        };
        
        // Return as object
        return self;
    };

    if (!window.AUDWidget_seats) {
        window.AUDWidget_seats = new Library();
        AUDWidget_seats.glvm = new AUDWidget_seats.GroupListViewModel()
    }
})();


/**
 * Init a AUDWidget_seats lib
 */
function init () {
    // populate example
    /*
    var gvm = new AUDWidget_seats.GroupViewModel("Group 1");
    gvm.people.push(new AUDWidget_seats.Person("1.1"));
    gvm.people.push(new AUDWidget_seats.Person("1.2"));
    gvlm.groups.push(gvm);

    gvm = new AUDWidget_seats.GroupViewModel("Group 2");
    gvm.people.push(new AUDWidget_seats.Person("2.1"));
    gvm.people.push(new AUDWidget_seats.Person("2.2"));
    gvlm.groups.push(gvm);

    gvlm.nypp.people.push(new AUDWidget_seats.Person("3.1"));
    */
    ko.applyBindings(AUDWidget_seats.glvm, $("#widget_seats")[0]);
}


$(document).ready(function () {
    init();
});

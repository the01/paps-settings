"use strict";

(function () {
    "use strict";

    var Library = function () {
        var self = this;
        this.version = "0.1.0";

        /**
         * Make an ajax request and return the request object
         *
         * @param {String}  uri                     make request to
         * @param {String}  [method="GET"]          HTTP method (GET/POST/PUT/..) (default: GET)
         * @param {Object}  [data=undefined]        data to be transmitted (only with POST or put)
         * @param {Boolean} [asyncFlag=true]        request asynchronously (default: true)
         * @param {String}  [dataType="json"]       set data type (formats data to json anyway)
         * @returns {Promise} JQuery ajax call return
         */
        this.ajaxRest = function (uri, method, data, asyncFlag, dataType) {
            console.debug(uri);
            if (method === undefined) {
                method = "GET";
            }
            if (asyncFlag === undefined) {
                asyncFlag = true;
            }
            if (dataType === undefined) {
                dataType = "json";
            }

            var request = {
                url: uri,
                type: method,
                //accepts: "application/json",
                //contentType: "application/json",
                /*headers: {
                 Accept: "application/json; charset=utf-8"
                 },
                 */
                cache: false,
                dataType: dataType,
                async: asyncFlag,
                error: function (jqXHR, textStatus, errorThrown) {
                    console.error("ajax error " + jqXHR.status);
                    console.error("text " + jqXHR.statusText);
                    console.error("code " + jqXHR.statusCode());
                    console.error(textStatus);
                    console.error(errorThrown);
                }
            };

            if (method == "POST" || method == "PUT") {
                request.contentType = "application/json";
                request.data = JSON.stringify(data);
            }
            // console.log("Ajax request: " + uri);
            return $.ajax(request);
        };
        
        function loader(url, element) {
            // Based on code from https://raw.githubusercontent.com/urish/angular-load by Uri Shaked (2016-02-03)
            var deferred = $.Deferred();

            element.onload = element.onreadystatechange = function (e) {
                if (element.readyState && element.readyState !== "complete" && element.readyState !== "loaded") {
                    return;
                }

                setTimeout(function () {
                    deferred.resolve(e);
                }, 0);
            };
            element.onerror = function (e) {
                setTimeout(function () {
                    deferred.reject(e);
                }, 0);
            };

            return deferred.promise();
        }

        /**
         * Dynamically loads the given script
         *
         * @param {string} src The url of the script to load dynamically
         * @param {string} loadClass Which class name to attach
         * @returns {Promise} Promise that will be resolved once the script has been loaded.
         */
        this.loadScript = function (src, loadClass) {
            var script = document.createElement("script");
            script.src = src;
            script.className += loadClass;
            document.body.appendChild(script);

            return loader(src, script);
        };

        /**
         * Dynamically loads the given CSS file
         *
         * @param {string} src The url of the CSS to load dynamically
         * @param {string} loadClass Which class name to attach
         * @returns {Promise} Promise that will be resolved once the CSS file has been loaded.
         */
        this.loadCSS = function (src, loadClass) {
            var style = document.createElement("link");
            style.rel = "stylesheet";
            style.type = "text/css";
            style.className += loadClass;
            style.href = src;
            document.head.appendChild(style);

            return loader(src, style);
        };

        /**
         * Dynamically loads the given html file
         *
         * @param {string} src The url of the html to load dynamically
         * @param {object} node The node to load the html into
         * @returns {Promise} Promise that will be resolved once the CSS file has been loaded.
         */
        this.loadHTML = function (src, node) {
            var deferred = $.Deferred();
            node.load(src, function(response, status, xhr) {
                if (status == "error") {
                    // console.error("Sorry but there was an error: " + xhr.status + " " + xhr.statusText);
                    deferred.reject(response, status, xhr);
                }
                else {
                    deferred.resolve(response, status, xhr);
                }
            });
            var promise = loader(src, node);
            promise.then(function (e) {
               deferred.resolve(e); 
            }, function (e) {
                deferred.reject(e);
            });
            return deferred.promise();
        };

        this.resource_load = function (key, api_uri, load_node, load_class) {
            var ext = key.substr((key.lastIndexOf(".") + 1));
            var self = this;
            var deferred = $.Deferred();

            function loadSucceed(e) {
                deferred.resolve(e);
            }

            function loadFailed(e) {
                deferred.reject(e);
            }

            this.ajaxRest(api_uri, "GET", undefined, false).then(function (data) {
                var resource = data.resource;
                var promise = null;

                if (resource.hasOwnProperty("uri")) {
                    var uri = resource.uri;

                    //console.info("Loading resource: " + uri);
                    switch (ext) {
                        case "htm":
                        case "xhtml":
                        case "html":
                            // loadHTML
                            promise = self.loadHTML(uri, load_node);
                            break;
                        case "css":
                            // loadCSS
                            promise = self.loadCSS(uri, load_class);
                            break;
                        case "js":
                            // loadScript
                            promise = self.loadScript(uri, load_class);
                            break;
                        default:
                            break;
                    }
                }
                if (promise != null) {
                    promise.then(loadSucceed, loadFailed);
                }
            }, loadFailed);

            return deferred.promise();
        };
        // Return as object
        return self;
    };

    if (!window.AUDUtils) {
        window.AUDUtils = new Library();
    }
})();


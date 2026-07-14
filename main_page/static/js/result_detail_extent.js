(function () {
    function initExtentMap() {
        var dataEl = document.getElementById("topic-extent-data");
        var mapEl = document.getElementById("topic-extent-map");
        if (!dataEl || !mapEl || typeof L === "undefined") {
            return;
        }

        var geom;
        try {
            geom = JSON.parse(dataEl.textContent);
        } catch (err) {
            return;
        }

        var attribution =
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
        var map = L.map(mapEl, {
            scrollWheelZoom: false,
            attributionControl: true,
            zoomControl: true,
        });

        L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png", {
            attribution: attribution,
            subdomains: "abcd",
            maxZoom: 19,
        }).addTo(map);

        var layer = L.geoJSON(geom, {
            style: {
                color: "#DF1B12",
                weight: 2,
                fillColor: "#DF1B12",
                fillOpacity: 0.12,
            },
        }).addTo(map);

        if (layer.getBounds().isValid()) {
            map.fitBounds(layer.getBounds(), { padding: [12, 12], maxZoom: 8 });
        }

        window.requestAnimationFrame(function () {
            map.invalidateSize();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initExtentMap);
    } else {
        initExtentMap();
    }
})();

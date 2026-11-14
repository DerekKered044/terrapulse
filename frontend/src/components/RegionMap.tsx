"use client";

import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Map as MlMap, GeoJSONSource, Marker } from "maplibre-gl";
import type { OverviewRow } from "@/lib/api";
import { trendColor } from "@/lib/format";

type Props = { rows: OverviewRow[]; selected: string; onSelect: (id: string) => void };

// NASA GIBS Blue Marble imagery (no key required).
const GIBS =
  "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg";

function toGeoJSON(rows: OverviewRow[], selected: string) {
  return {
    type: "FeatureCollection" as const,
    features: rows.map((r) => {
      const [w, s, e, n] = r.bbox;
      return {
        type: "Feature" as const,
        properties: {
          id: r.region,
          color: trendColor(r.slope_per_decade, r.p_value < 0.05 && r.mk_p_value < 0.05),
          selected: r.region === selected,
        },
        geometry: { type: "Polygon" as const, coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]] },
      };
    }),
  };
}

export default function RegionMap({ rows, selected, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const markers = useRef<Marker[]>([]);
  const latest = useRef({ rows, selected, onSelect });

  useEffect(() => {
    latest.current = { rows, selected, onSelect };
    const map = mapRef.current;
    const src = map?.getSource("regions") as GeoJSONSource | undefined;
    if (src) src.setData(toGeoJSON(rows, selected));
    markers.current.forEach((m) => {
      const el = m.getElement();
      el.dataset.selected = String(el.dataset.id === selected);
    });
  }, [rows, selected, onSelect]);

  useEffect(() => {
    let disposed = false;
    import("maplibre-gl").then((ml) => {
      if (disposed || !container.current) return;
      ml.setWorkerUrl(`${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/maplibre-gl-worker.mjs`);
      const map = new ml.Map({
        container: container.current,
        style: {
          version: 8,
          sources: {
            gibs: { type: "raster", tiles: [GIBS], tileSize: 256, maxzoom: 8, attribution: "Imagery: NASA GIBS / Blue Marble" },
          },
          layers: [
            { id: "bg", type: "background", paint: { "background-color": "#020617" } },
            { id: "gibs", type: "raster", source: "gibs", paint: { "raster-brightness-max": 0.8, "raster-saturation": -0.25 } },
          ],
        },
        center: [15, 22],
        zoom: 0.6,
        minZoom: 0,
        maxZoom: 6,
        attributionControl: { compact: true },
        renderWorldCopies: false,
      });
      mapRef.current = map;
      map.addControl(new ml.NavigationControl({ showCompass: false }), "top-right");
      map.on("load", () => {
        const { rows, selected } = latest.current;
        map.addSource("regions", { type: "geojson", data: toGeoJSON(rows, selected) });
        map.addLayer({
          id: "region-fill",
          type: "fill",
          source: "regions",
          paint: { "fill-color": ["get", "color"], "fill-opacity": ["case", ["get", "selected"], 0.6, 0.35] },
        });
        map.addLayer({
          id: "region-line",
          type: "line",
          source: "regions",
          paint: {
            "line-color": ["case", ["get", "selected"], "#ffffff", ["get", "color"]],
            "line-width": ["case", ["get", "selected"], 3, 1.5],
          },
        });
        map.on("click", "region-fill", (e) => {
          const id = e.features?.[0]?.properties?.id;
          if (id) latest.current.onSelect(String(id));
        });
        map.on("mouseenter", "region-fill", () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", "region-fill", () => (map.getCanvas().style.cursor = ""));
        for (const r of rows) {
          const el = document.createElement("button");
          el.type = "button";
          el.className = "tp-map-label";
          el.textContent = r.name;
          el.dataset.id = r.region;
          el.dataset.selected = String(r.region === selected);
          el.addEventListener("click", (ev) => {
            ev.stopPropagation();
            latest.current.onSelect(r.region);
          });
          const [w, , e, n] = r.bbox;
          markers.current.push(new ml.Marker({ element: el, anchor: "bottom" }).setLngLat([(w + e) / 2, n]).addTo(map));
        }
      });
    });
    return () => {
      disposed = true;
      markers.current.forEach((m) => m.remove());
      markers.current = [];
      mapRef.current?.remove();
      mapRef.current = null;
    };
    // The map is created once; later prop changes are applied by the effect above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows.length > 0]);

  return <div ref={container} className="h-full w-full" aria-label="Map of supported regions. Select a region to analyse it." />;
}

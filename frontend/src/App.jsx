import {
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Building2,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Crosshair,
  Database,
  Download,
  FileText,
  Filter,
  FlaskConical,
  Gauge,
  History as HistoryIcon,
  Layers3,
  LayoutDashboard,
  Map as MapIcon,
  MapPin,
  Menu,
  RefreshCw,
  Search,
  Shield,
  SlidersHorizontal,
  Target,
  TrendingUp,
  X,
} from "lucide-react";

import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  ZoomControl,
  useMap,
} from "react-leaflet";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";

const API_BASE = "http://127.0.0.1:8000";

const AnalysisContext = createContext(null);
const ANALYSIS_DEFAULTS = {
  city: "All Cities",
  severity: "All Severities",
  startYear: 2022,
  endYear: 2025,
};
const ANALYSIS_CITIES = [
  "Bangalore", "Chandigarh", "Chennai", "Delhi",
  "Hyderabad", "Kolkata", "Mumbai", "Pune",
];

function useAnalysisContext() {
  return useContext(AnalysisContext);
}

function contextQuery(context, extra = {}) {
  const params = new URLSearchParams();
  if (context?.city && context.city !== "All Cities") params.set("city", context.city);
  if (context?.severity && context.severity !== "All Severities") params.set("severity", context.severity);
  params.set("start_date", `${context?.startYear || 2022}-01-01`);
  params.set("end_date", `${context?.endYear || 2025}-12-31`);
  Object.entries(extra).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") params.set(key, value);
  });
  return params.toString();
}

const INDIA_CENTER = [22.5, 78.9];

const navigation = [
  {
    label: "Overview",
    path: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Live Map",
    path: "/map",
    icon: MapIcon,
  },
  {
    label: "Hotspots",
    path: "/hotspots",
    icon: Activity,
  },
  {
    label: "Cities",
    path: "/cities",
    icon: Building2,
  },
  {
    label: "Risk Factors",
    path: "/factors",
    icon: BarChart3,
  },
  {
    label: "History",
    path: "/history",
    icon: HistoryIcon,
  },
  {
    label: "Road Safety Lab",
    path: "/lab",
    icon: FlaskConical,
  },
  {
    label: "Reports",
    path: "/reports",
    icon: FileText,
  },
  {
    label: "Methodology",
    path: "/methodology",
    icon: SlidersHorizontal,
  },
];

const pageMeta = {
  "/": {
    eyebrow: "ROAD INTELLIGENCE PLATFORM",
    title: "RoadSafe India",
    description:
      "Spatial accident intelligence for understanding where road risk concentrates.",
  },
  "/map": {
    eyebrow: "SPATIAL INTELLIGENCE",
    title: "Live Map",
    description:
      "Explore accident locations, DBSCAN hotspots and historical reference layers.",
  },
  "/hotspots": {
    eyebrow: "HOTSPOT INTELLIGENCE",
    title: "Hotspot Explorer",
    description:
      "Investigate spatial clusters and the indicators that make them important.",
  },
  "/cities": {
    eyebrow: "CITY INTELLIGENCE",
    title: "Cities",
    description:
      "Compare accident patterns and spatial clustering across analysed cities.",
  },
  "/factors": {
    eyebrow: "RISK INTELLIGENCE",
    title: "Risk Factors",
    description:
      "Explore environmental, road and numerical factors represented in the dataset.",
  },
  "/history": {
    eyebrow: "HISTORICAL REFERENCE",
    title: "Kerala History",
    description:
      "Explore the historical Kerala black-spot dataset as a separate regional layer.",
  },
  "/lab": {
    eyebrow: "ANALYSIS WORKSPACE",
    title: "Road Safety Lab",
    description:
      "Explore hotspot distributions and analytical scenarios without altering the source data.",
  },
  "/reports": {
    eyebrow: "DECISION SUPPORT",
    title: "Reports",
    description:
      "Turn RoadSafe India intelligence into concise analytical outputs.",
  },
  "/methodology": {
    eyebrow: "TRANSPARENCY",
    title: "Methodology",
    description:
      "Understand the data, DBSCAN workflow and interpretation behind RoadSafe India.",
  },
};

/* =========================================================
   HELPERS
   ========================================================= */

function formatNumber(value) {
  if (
    value === null ||
    value === undefined ||
    value === "" ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  return Number(value).toLocaleString("en-IN");
}

function formatDecimal(value, digits = 2) {
  if (
    value === null ||
    value === undefined ||
    value === "" ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  return Number(value).toFixed(digits);
}

function formatPercent(value, digits = 1) {
  if (
    value === null ||
    value === undefined ||
    value === "" ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function formatRiskProfile(value) {
  if (!value) {
    return "Unclassified";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function humanize(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  return String(value)
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function safeNumber(value, fallback = 0) {
  const parsed = Number(value);

  return Number.isFinite(parsed) ? parsed : fallback;
}

function LoadingState({ label = "Loading intelligence..." }) {
  return (
    <div className="overview-loading">
      <div className="loading-ring" />
      <span>{label}</span>
    </div>
  );
}

function ErrorState({ title, message, onRetry }) {
  return (
    <div className="overview-error">
      <div className="error-icon">
        <AlertTriangle size={20} />
      </div>

      <div>
        <strong>{title}</strong>

        <p>{message}</p>

        <span>
          Make sure FastAPI is running on port 8000.
        </span>

        {onRetry && (
          <button
            type="button"
            className="secondary-action"
            onClick={onRetry}
          >
            <RefreshCw size={14} />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

function EmptyState({
  icon: Icon = Database,
  title = "No data",
  description = "No matching records are available.",
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <Icon size={21} />
      </div>

      <strong>{title}</strong>

      <p>{description}</p>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  detail,
  accent = false,
}) {
  return (
    <div
      className={`stat-card ${
        accent ? "stat-card-accent" : ""
      }`}
    >
      <div className="stat-card-top">
        <div className="stat-icon">
          <Icon size={17} strokeWidth={1.7} />
        </div>

        <span className="stat-label">
          {label}
        </span>
      </div>

      <div className="stat-value">
        {value}
      </div>

      <div className="stat-detail">
        {detail}
      </div>
    </div>
  );
}

function SectionHeader({
  kicker,
  title,
  meta,
}) {
  return (
    <div className="panel-header">
      <div>
        {kicker && (
          <span className="panel-kicker">
            {kicker}
          </span>
        )}

        <h3>{title}</h3>
      </div>

      {meta && (
        <div className="panel-meta">
          {meta}
        </div>
      )}
    </div>
  );
}

/* =========================================================
   OVERVIEW
   ========================================================= */

function Overview() {
  const { analysisContext } = useAnalysisContext();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadOverview() {
    try {
      setLoading(true);
      setError("");

      const [response, hotspotsResponse] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard`),
        fetch(`${API_BASE}/api/hotspots?${contextQuery(analysisContext)}`),
      ]);

      if (!response.ok) {
        throw new Error("Dashboard API request failed.");
      }

      const [data, hotspotData] = await Promise.all([response.json(), hotspotsResponse.json()]);
      const contextResponse = await fetch(`${API_BASE}/api/analysis/context?${contextQuery(analysisContext)}`);
      if (!contextResponse.ok) throw new Error("Analysis context request failed.");
      const contextData = await contextResponse.json();
      const contextHotspots = hotspotData.hotspots || [];
      const cityLookup = new Map();
      contextHotspots.forEach((hotspot) => {
        const current = cityLookup.get(hotspot.city) || { hotspot_candidates: 0, multiple_indicator_hotspots: 0 };
        current.hotspot_candidates += 1;
        if (hotspot.risk_profile === "multiple_high_risk_indicators") current.multiple_indicator_hotspots += 1;
        cityLookup.set(hotspot.city, current);
      });
      setDashboard({
        ...data,
        cities: contextData.cities.map((city) => ({ ...city, hotspot_candidates: cityLookup.get(city.city)?.hotspot_candidates || 0, multiple_indicator_hotspots: cityLookup.get(city.city)?.multiple_indicator_hotspots || 0 })),
        overview: {
          ...data.overview,
          total_accidents: contextData.summary.accidents,
          spatial_clusters: contextData.summary.spatial_clusters,
          hotspot_candidates: contextHotspots.length,
          multiple_indicator_hotspots: contextHotspots.filter((hotspot) => hotspot.risk_profile === "multiple_high_risk_indicators").length,
        },
      });
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Unable to connect to the RoadSafe India intelligence API.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOverview();
  }, [analysisContext.city, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);

  if (loading) {
    return (
      <LoadingState label="Loading road intelligence..." />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Intelligence API unavailable"
        message={error}
        onRetry={loadOverview}
      />
    );
  }

  const overview = dashboard?.overview || {};

  const cityRows = Array.isArray(dashboard?.cities)
    ? dashboard.cities
    : [];

  const sortedCities = [...cityRows].sort(
    (a, b) =>
      safeNumber(b.accidents) -
      safeNumber(a.accidents),
  );

  return (
    <div className="overview">
      <section className="overview-intro">
        <div>
          <span className="section-kicker">
            CURRENT DATASET
          </span>

          <h2>
            India Road Risk Overview
          </h2>
        </div>

        <div className="dataset-badge">
          <span className="status-dot" />
          {dashboard?.dataset?.cities_count ?? 8} ANALYSED
          CITIES
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          icon={AlertTriangle}
          label="ACCIDENT RECORDS"
          value={formatNumber(
            overview.total_accidents,
          )}
          detail="Contemporary accident dataset"
        />

        <StatCard
          icon={Layers3}
          label="SPATIAL CLUSTERS"
          value={formatNumber(
            overview.spatial_clusters,
          )}
          detail="DBSCAN clusters across analysed cities"
          accent
        />

        <StatCard
          icon={MapPin}
          label="HOTSPOT CANDIDATES"
          value={formatNumber(
            overview.hotspot_candidates,
          )}
          detail="Clusters meeting hotspot criteria"
        />

        <StatCard
          icon={TrendingUp}
          label="MULTI-INDICATOR"
          value={formatNumber(
            overview.multiple_indicator_hotspots,
          )}
          detail="Hotspots with multiple high-risk indicators"
        />
      </section>

      <section className="overview-grid">
        <div className="panel">
          <SectionHeader
            kicker="CITY COVERAGE"
            title="Analysed cities"
            meta={`${cityRows.length} cities`}
          />

          <div className="city-table">
            <div className="city-table-head">
              <span>CITY</span>
              <span>ACCIDENTS</span>
              <span>CLUSTERED</span>
              <span>STATUS</span>
            </div>

            {sortedCities.map((city, index) => (
              <div
                className="city-table-row"
                key={`${city.city}-${index}`}
              >
                <div className="city-name">
                  <span className="city-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <strong>{city.city}</strong>
                </div>

                <span>
                  {formatNumber(city.accidents)}
                </span>

                <span>
                  {formatNumber(
                    city.clustered_records,
                  )}
                </span>

                <span className="city-status">
                  <span className="status-dot" />
                  {city.city === "Chandigarh" ? "Descriptive only" : "Clustered"}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel overview-scope-panel">
          <SectionHeader
            kicker="DATA SCOPE"
            title="What RoadSafe India covers"
          />

          <div className="scope-list">
            <div className="scope-item">
              <div className="scope-icon">
                <Database size={17} />
              </div>

              <div>
                <strong>
                  Contemporary accident dataset
                </strong>

                <p>
                  {dashboard?.dataset?.cities_count ?? 8} selected
                  Indian cities, from{" "}
                  {dashboard?.dataset?.start_date ?? "2022-01-01"}{" "}
                  to{" "}
                  {dashboard?.dataset?.end_date ?? "2025-04-15"}.
                </p>
              </div>
            </div>

            <div className="scope-item">
              <div className="scope-icon">
                <Layers3 size={17} />
              </div>

              <div>
                <strong>
                  Spatial clustering
                </strong>

                <p>
                  City-wise DBSCAN analysis is used to identify
                  spatially concentrated accident records.
                </p>
              </div>
            </div>

            <div className="scope-item">
              <div className="scope-icon">
                <HistoryIcon size={17} />
              </div>

              <div>
                <strong>
                  Historical Kerala reference
                </strong>

                <p>
                  The Kerala black-spot dataset is maintained
                  separately from the contemporary city dataset.
                </p>
              </div>
            </div>
          </div>

          <NavLink
            to="/methodology"
            className="panel-link"
          >
            Explore methodology
            <ChevronRight size={15} />
          </NavLink>
        </div>
      </section>
    </div>
  );
}

/* =========================================================
   MAP
   ========================================================= */

function MapViewportController({
  focusPoint,
  selectedCity,
}) {
  const map = useMap();

  useEffect(() => {
    if (
      focusPoint &&
      Number.isFinite(Number(focusPoint[0])) &&
      Number.isFinite(Number(focusPoint[1]))
    ) {
      map.flyTo(
        [
          Number(focusPoint[0]),
          Number(focusPoint[1]),
        ],
        12,
        {
          duration: 0.8,
        },
      );

      return;
    }

    if (selectedCity !== "All Cities") {
      return;
    }

    map.setView(INDIA_CENTER, 5);
  }, [map, focusPoint, selectedCity]);

  return null;
}

function AccidentMarker({ accident }) {
  const severity = String(
    accident.severity || "",
  ).toLowerCase();

  const radius =
    severity === "fatal"
      ? 5
      : severity === "major"
        ? 4.5
        : 4;

  const location =
    accident.location || {};

  const latitude = Number(location.latitude);
  const longitude = Number(location.longitude);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  return (
    <CircleMarker
      center={[latitude, longitude]}
      radius={radius}
      pathOptions={{
        color: "#ffffff",
        weight: 0.8,
        fillColor:
          severity === "fatal"
            ? "#ff6b6b"
            : severity === "major"
              ? "#f2c96d"
              : "#b9ff65",
        fillOpacity: 0.55,
      }}
    >
      <Popup>
        <div className="map-popup">
          <div className="popup-kicker">
            ACCIDENT RECORD
          </div>

          <strong>
            {accident.city || "Indian city"}
          </strong>

          <div className="popup-grid">
            <span>Severity</span>
            <b>{humanize(accident.severity)}</b>

            <span>Vehicles</span>
            <b>
              {formatNumber(
                accident.number_of_vehicles ??
                  accident.vehicles,
              )}
            </b>

            <span>Casualties</span>
            <b>
              {formatNumber(
                accident.number_of_casualties ??
                  accident.casualties,
              )}
            </b>
          </div>
        </div>
      </Popup>
    </CircleMarker>
  );
}

function HotspotMarker({ hotspot, onSelect }) {
  const location =
    hotspot.location || {};

  const latitude = Number(location.latitude);
  const longitude = Number(location.longitude);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  const stats =
    hotspot.statistics || {};

  const indicators =
    hotspot.risk_indicators || {};

  return (
    <CircleMarker
      center={[latitude, longitude]}
      radius={9}
      pathOptions={{
        color: "#b9ff65",
        weight: 2,
        fillColor: "#b9ff65",
        fillOpacity: 0.12,
      }}
      eventHandlers={{ click: () => onSelect?.(hotspot) }}
    >
      <Popup>
        <div className="map-popup">
          <div className="popup-kicker">
            HOTSPOT CANDIDATE
          </div>

          <strong>
            {hotspot.city}
          </strong>

          <div className="popup-cluster">
            DBSCAN CLUSTER {hotspot.cluster_id}
          </div>

          <div className="popup-grid">
            <span>Accidents</span>
            <b>
              {formatNumber(
                stats.accident_count,
              )}
            </b>

            <span>Casualties</span>
            <b>
              {formatNumber(
                stats.total_casualties,
              )}
            </b>

            <span>Mean risk</span>
            <b>
              {formatDecimal(
                stats.mean_risk_score,
              )}
            </b>

            <span>Fatal</span>
            <b>
              {formatNumber(
                stats.fatal_accidents,
              )}
            </b>
          </div>

          <div className="popup-risk-profile">
            {formatRiskProfile(
              hotspot.risk_profile,
            )}
          </div>

          <div className="popup-indicators">
            {indicators.high_accident_density && (
              <span>HIGH DENSITY</span>
            )}

            {indicators.high_casualty_burden && (
              <span>HIGH CASUALTY</span>
            )}

            {indicators.high_fatality_proportion && (
              <span>HIGH FATALITY</span>
            )}

            {indicators.high_mean_risk_score && (
              <span>HIGH RISK</span>
            )}
          </div>
        </div>
      </Popup>
    </CircleMarker>
  );
}

function HistoricalMarker({ record }) {
  const start =
    record.start || {};

  const latitude = Number(start.latitude);
  const longitude = Number(start.longitude);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  return (
    <CircleMarker
      center={[latitude, longitude]}
      radius={7}
      pathOptions={{
        color: "#f2c96d",
        weight: 1.2,
        fillColor: "#f2c96d",
        fillOpacity: 0.18,
      }}
    >
      <Popup>
        <div className="map-popup">
          <div className="popup-kicker">
            HISTORICAL BLACK SPOT
          </div>

          <strong>
            {record.location || "Historical location"}
          </strong>

          <div className="popup-grid">
            <span>District</span>
            <b>{record.district}</b>

            <span>Police station</span>
            <b>{record.police_station}</b>

            <span>Road</span>
            <b>{record.road_name}</b>

            <span>Road number</span>
            <b>{record.road_number}</b>
          </div>
        </div>
      </Popup>
    </CircleMarker>
  );
}

function LiveMap() {
  const location = useLocation();
  const navigate = useNavigate();
  const { analysisContext, setAnalysisContext } = useAnalysisContext();

  const [accidents, setAccidents] = useState([]);
  const [accidentTotal, setAccidentTotal] =
    useState(0);
  const [hotspots, setHotspots] = useState([]);
  const [history, setHistory] = useState([]);

  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState("");

  const selectedCity = analysisContext.city;

  const [showAccidents, setShowAccidents] =
    useState(true);
  const [showHotspots, setShowHotspots] =
    useState(true);
  const [showHistory, setShowHistory] =
    useState(true);

  const [focusPoint, setFocusPoint] =
    useState(null);
  const [selectedHotspot, setSelectedHotspot] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  async function loadMapData() {
    try {
      setLoading(true);
      setError("");

      const [
        accidentsResponse,
        hotspotsResponse,
        historyResponse,
      ] = await Promise.all([
        fetch(
          `${API_BASE}/api/accidents?${contextQuery(analysisContext, { limit: 1000, offset: 0 })}`,
        ),
        fetch(`${API_BASE}/api/hotspots?${contextQuery(analysisContext)}`),
        fetch(`${API_BASE}/api/history/kerala`),
      ]);

      if (!accidentsResponse.ok) {
        throw new Error(
          "Accidents API request failed.",
        );
      }

      if (!hotspotsResponse.ok) {
        throw new Error(
          "Hotspots API request failed.",
        );
      }

      if (!historyResponse.ok) {
        throw new Error(
          "History API request failed.",
        );
      }

      const accidentsData =
        await accidentsResponse.json();

      const hotspotsData =
        await hotspotsResponse.json();

      const historyData =
        await historyResponse.json();

      setAccidents(
        Array.isArray(
          accidentsData.accidents,
        )
          ? accidentsData.accidents
          : [],
      );

      setAccidentTotal(
        safeNumber(
          accidentsData.total,
          accidentsData.count || 0,
        ),
      );

      setHotspots(
        Array.isArray(
          hotspotsData.hotspots,
        )
          ? hotspotsData.hotspots
          : [],
      );

      setHistory(
        Array.isArray(
          historyData.records,
        )
          ? historyData.records
          : [],
      );
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Unable to load spatial intelligence from the API.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMapData();
  }, [analysisContext.city, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);

  useEffect(() => {
    if (!isPlaying) return undefined;
    const timer = window.setInterval(() => {
      setAnalysisContext((current) => {
        const next = current.endYear >= 2025 ? 2022 : current.endYear + 1;
        return { ...current, startYear: next, endYear: next };
      });
    }, 1700);
    return () => window.clearInterval(timer);
  }, [isPlaying, setAnalysisContext]);

  useEffect(() => {
    const focus =
      location.state?.focus;

    if (
      focus?.latitude !== undefined &&
      focus?.longitude !== undefined
    ) {
      setFocusPoint([
        Number(focus.latitude),
        Number(focus.longitude),
      ]);
    }
  }, [location.state]);

  const cities = useMemo(() => {
    const set = new Set();

    hotspots.forEach((item) => {
      if (item.city) {
        set.add(item.city);
      }
    });

    accidents.forEach((item) => {
      if (item.city) {
        set.add(item.city);
      }
    });

    return Array.from(set).sort();
  }, [hotspots, accidents]);

  const filteredAccidents = useMemo(() => {
    if (selectedCity === "All Cities") {
      return accidents;
    }

    return accidents.filter(
      (accident) =>
        accident.city === selectedCity,
    );
  }, [accidents, selectedCity]);

  const filteredHotspots = useMemo(() => {
    if (selectedCity === "All Cities") {
      return hotspots;
    }

    return hotspots.filter(
      (hotspot) =>
        hotspot.city === selectedCity,
    );
  }, [hotspots, selectedCity]);
  const visibleAccidents = filteredAccidents.slice(0, 100);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const city = params.get("city");
    const cluster = Number(params.get("cluster"));
    if (city && city !== analysisContext.city) setAnalysisContext((current) => ({ ...current, city }));
    if (cluster) {
      const match = hotspots.find((item) => item.city === city && item.cluster_id === cluster);
      if (match) setSelectedHotspot(match);
    }
  }, [location.search, hotspots]);

  if (loading) {
    return (
      <LoadingState label="Loading spatial intelligence..." />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Map data unavailable"
        message={error}
        onRetry={loadMapData}
      />
    );
  }

  return (
    <div className="live-map-page">
      <div className="map-toolbar">
        <div className="map-toolbar-left">
          <div className="map-tool-title">
            <Crosshair size={15} />
            <span>SPATIAL VIEW</span>
          </div>

          <div className="map-divider" />

          <label className="city-filter">
            <Filter size={13} />

            <select
              value={selectedCity}
              onChange={(event) => {
                setAnalysisContext((current) => ({ ...current, city: event.target.value }));
                setFocusPoint(null);
                setSelectedHotspot(null);
              }}
            >
              <option>All Cities</option>

              {cities.map((city) => (
                <option
                  key={city}
                  value={city}
                >
                  {city}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="map-timeline-control">
          <button type="button" className="timeline-play" onClick={() => setIsPlaying((playing) => !playing)} aria-label={isPlaying ? "Pause timeline" : "Play timeline"}>{isPlaying ? "Ⅱ" : "▶"}</button>
          <span>YEAR</span>
          <input aria-label="Map timeline year" type="range" min="2022" max="2025" step="1" value={analysisContext.endYear} onChange={(event) => { const year = Number(event.target.value); setAnalysisContext((current) => ({ ...current, startYear: year, endYear: year })); }} />
          <b>{analysisContext.startYear === analysisContext.endYear ? analysisContext.endYear : `${analysisContext.startYear}–${analysisContext.endYear}`}</b>
        </div>

        <div className="map-toolbar-stats">
          <span>
            <b>
              {formatNumber(
                visibleAccidents.length,
              )}
            </b>{" "}
            shown (limit 100)
          </span>

          <span>
            <b>
              {formatNumber(
                accidentTotal,
              )}
            </b>{" "}
            total in dataset
          </span>

          <span>
            <b>
              {formatNumber(
                filteredHotspots.length,
              )}
            </b>{" "}
            hotspots
          </span>
        </div>
      </div>

      <div className="map-workspace">
        <div className="map-container-shell">
          <MapContainer
            center={INDIA_CENTER}
            zoom={5}
            minZoom={4}
            maxZoom={15}
            zoomControl={false}
            className="roadsafe-map"
          >
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url={`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${import.meta.env.VITE_CARTO_API_KEY}`}
            />

            <ZoomControl position="bottomright" />

            <MapViewportController
              focusPoint={focusPoint}
              selectedCity={selectedCity}
            />

            {showAccidents &&
                    filteredAccidents.slice(0, 100).map(
                (accident, index) => (
                  <AccidentMarker
                    key={
                      accident.accident_id ||
                      accident.id ||
                      index
                    }
                    accident={accident}
                  />
                ),
              )}

            {showHotspots &&
              filteredHotspots.map(
                (hotspot) => (
                    <HotspotMarker
                    key={`${hotspot.city}-${hotspot.cluster_id}`}
                    hotspot={hotspot}
                      onSelect={setSelectedHotspot}
                  />
                ),
              )}

            {showHistory &&
              selectedCity === "All Cities" &&
              history.map(
                (record, index) => (
                  <HistoricalMarker
                    key={`${record.sl_no}-${index}`}
                    record={record}
                  />
                ),
              )}
          </MapContainer>

          <div className="map-overlay-title">
            <img src="/assets/roadsafe-india-mark.png" alt="RoadSafe India" className="map-overlay-mark" />
            <strong>Spatial Risk Monitor</strong>
          </div>

          <div className="map-legend">
            <div className="legend-title">
              MAP LAYERS
            </div>

            <label className="legend-toggle">
              <input
                type="checkbox"
                checked={showAccidents}
                onChange={(event) =>
                  setShowAccidents(
                    event.target.checked,
                  )
                }
              />

              <span className="legend-dot accident-dot" />

              <span>
                Accident locations
              </span>
            </label>

            <label className="legend-toggle">
              <input
                type="checkbox"
                checked={showHotspots}
                onChange={(event) =>
                  setShowHotspots(
                    event.target.checked,
                  )
                }
              />

              <span className="legend-dot hotspot-dot" />

              <span>
                Hotspot candidates
              </span>
            </label>

            <label className="legend-toggle">
              <input
                type="checkbox"
                checked={showHistory}
                onChange={(event) =>
                  setShowHistory(
                    event.target.checked,
                  )
                }
              />

              <span className="legend-dot history-dot" />

              <span>
                Kerala historical layer
              </span>
            </label>
          </div>
        </div>

        <aside className="map-side-panel">
          {selectedHotspot ? (
            <div className="map-selected-hotspot">
              <div className="map-side-header"><span className="panel-kicker">SELECTED HOTSPOT</span><h3>{selectedHotspot.city}</h3><span className="detail-cluster">DBSCAN CLUSTER {selectedHotspot.cluster_id}</span></div>
              <div className="detail-metric-grid">
                <div><span>Accidents</span><strong>{formatNumber(selectedHotspot.statistics?.accident_count)}</strong></div>
                <div><span>Casualties</span><strong>{formatNumber(selectedHotspot.statistics?.total_casualties)}</strong></div>
                <div><span>Fatal</span><strong>{formatNumber(selectedHotspot.statistics?.fatal_accidents)}</strong></div>
                <div><span>Mean risk</span><strong>{formatDecimal(selectedHotspot.statistics?.mean_risk_score)}</strong></div>
              </div>
              <div className="popup-risk-profile">{formatRiskProfile(selectedHotspot.risk_profile)}</div>
              <button type="button" className="map-action-button" onClick={() => navigate(`/hotspots?city=${encodeURIComponent(selectedHotspot.city)}&cluster=${selectedHotspot.cluster_id}`)}>Open hotspot details <ChevronRight size={14} /></button>
              <button type="button" className="text-action" onClick={() => setSelectedHotspot(null)}>Back to map snapshot</button>
            </div>
          ) : (
          <>
          <div className="map-side-header">
            <span className="panel-kicker">
              SPATIAL INTELLIGENCE
            </span>

            <h3>Map snapshot</h3>
          </div>

          <div className="map-side-stat">
            <div className="map-side-stat-icon">
              <Database size={15} />
            </div>

            <div>
              <span>
                DISPLAYED ACCIDENTS
              </span>

              <strong>
                {formatNumber(
                  visibleAccidents.length,
                )}
              </strong>
            </div>
          </div>

          <div className="map-side-stat">
            <div className="map-side-stat-icon hotspot-icon">
              <Activity size={15} />
            </div>

            <div>
              <span>
                HOTSPOT CANDIDATES
              </span>

              <strong>
                {formatNumber(
                  filteredHotspots.length,
                )}
              </strong>
            </div>
          </div>

          <div className="map-side-stat">
            <div className="map-side-stat-icon history-icon">
              <HistoryIcon size={15} />
            </div>

            <div>
              <span>
                HISTORICAL RECORDS
              </span>

              <strong>
                {formatNumber(
                  history.length,
                )}
              </strong>
            </div>
          </div>

          <div className="map-side-divider" />

          <div className="map-side-note">
            <span className="status-dot" />

            <p>
              Accident records and cluster statistics use the active city, severity and date context. Cluster identity and risk profiles remain from the original full-period DBSCAN analysis. Records in scope: {" "}
              {formatNumber(
                accidentTotal,
              )}{" "}
              .
            </p>
          </div>

          <div className="map-side-footer">
            <span>DATA SOURCE</span>

            <strong>
              RoadSafe India API
            </strong>
          </div>
          </>
          )}
        </aside>
      </div>
    </div>
  );
}

/* =========================================================
   HOTSPOTS
   ========================================================= */

function Hotspots() {
  const navigate = useNavigate();
  const location = useLocation();
  const { analysisContext, setAnalysisContext } = useAnalysisContext();

  const [hotspots, setHotspots] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [selectedCity, setSelectedCity] =
    useState(analysisContext.city);

  const [selectedProfile, setSelectedProfile] =
    useState("All Profiles");

  const [minimumAccidents, setMinimumAccidents] =
    useState("0");

  const [searchTerm, setSearchTerm] =
    useState("");

  const [selectedHotspot, setSelectedHotspot] =
    useState(null);

  async function loadHotspots() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE}/api/hotspots?${contextQuery(analysisContext)}`,
      );

      if (!response.ok) {
        throw new Error(
          "Hotspots API request failed.",
        );
      }

      const data = await response.json();

      setHotspots(
        Array.isArray(data.hotspots)
          ? data.hotspots
          : [],
      );
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Unable to load hotspot intelligence from the API.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHotspots();
  }, [analysisContext.city, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);

  useEffect(() => setSelectedCity(analysisContext.city), [analysisContext.city]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const city = params.get("city");
    const cluster = Number(params.get("cluster"));
    if (city) {
      setSelectedCity(city);
      setAnalysisContext((current) => ({ ...current, city }));
    }
    if (cluster) {
      const match = hotspots.find((item) => item.city === city && item.cluster_id === cluster);
      if (match) setSelectedHotspot(match);
    }
  }, [location.search, hotspots]);

  const cities = useMemo(
    () =>
      Array.from(
        new Set(
          hotspots
            .map((item) => item.city)
            .filter(Boolean),
        ),
      ).sort(),
    [hotspots],
  );

  const profiles = useMemo(
    () =>
      Array.from(
        new Set(
          hotspots
            .map(
              (item) =>
                item.risk_profile,
            )
            .filter(Boolean),
        ),
      ).sort(),
    [hotspots],
  );

  const filteredHotspots = useMemo(() => {
    const query =
      searchTerm
        .trim()
        .toLowerCase();

    const minAccidents =
      Number(minimumAccidents);

    return hotspots.filter(
      (hotspot) => {
        const matchesCity =
          selectedCity ===
            "All Cities" ||
          hotspot.city ===
            selectedCity;

        const matchesProfile =
          selectedProfile ===
            "All Profiles" ||
          hotspot.risk_profile ===
            selectedProfile;

        const accidentCount =
          safeNumber(
            hotspot.statistics
              ?.accident_count,
          );

        const matchesMinimum =
          accidentCount >=
          minAccidents;

        const searchableText = [
          hotspot.city,
          hotspot.cluster_id,
          hotspot.risk_profile,
          hotspot.location
            ?.latitude,
          hotspot.location
            ?.longitude,
        ]
          .filter(
            (value) =>
              value !== null &&
              value !== undefined,
          )
          .join(" ")
          .toLowerCase();

        const matchesSearch =
          !query ||
          searchableText.includes(
            query,
          );

        return (
          matchesCity &&
          matchesProfile &&
          matchesMinimum &&
          matchesSearch
        );
      },
    );
  }, [
    hotspots,
    selectedCity,
    selectedProfile,
    minimumAccidents,
    searchTerm,
  ]);

  const multipleIndicatorCount =
    hotspots.filter(
      (hotspot) =>
        hotspot.risk_profile ===
        "multiple_high_risk_indicators",
    ).length;

  const singleIndicatorCount =
    hotspots.filter(
      (hotspot) =>
        hotspot.risk_profile ===
        "single_high_risk_indicator",
    ).length;

  const totalAccidentsInsideHotspots =
    hotspots.reduce(
      (total, hotspot) =>
        total +
        safeNumber(
          hotspot.statistics
            ?.accident_count,
        ),
      0,
    );

  const selectedStats =
    selectedHotspot?.statistics ||
    {};

  const selectedSeverity =
    selectedHotspot?.severity ||
    {};

  const selectedIndicators =
    selectedHotspot?.risk_indicators ||
    {};

  function openOnMap(hotspot) {
    const latitude =
      hotspot.location?.latitude;

    const longitude =
      hotspot.location?.longitude;

    if (
      latitude === undefined ||
      longitude === undefined
    ) {
      return;
    }

    navigate(`/map?city=${encodeURIComponent(hotspot.city)}&cluster=${hotspot.cluster_id}`, {
      state: {
        focus: {
          latitude,
          longitude,
        },
      },
    });
  }

  if (loading) {
    return (
      <LoadingState label="Loading hotspot intelligence..." />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Hotspot intelligence unavailable"
        message={error}
        onRetry={loadHotspots}
      />
    );
  }

  return (
    <div className="hotspots-page">
      <div className="context-explainer">Cluster identities are the existing DBSCAN outputs. City, severity and date context narrow the records and statistics inside those clusters; DBSCAN and full-period risk profiles are not recalculated.</div>
      <section className="hotspot-summary-grid">
        <div className="hotspot-stat">
          <div className="hotspot-stat-label">
            <Target size={14} />
            HOTSPOT CANDIDATES
          </div>

          <div className="hotspot-stat-value">
            {formatNumber(
              hotspots.length,
            )}
          </div>

          <div className="hotspot-stat-detail">
            Spatial clusters meeting candidate criteria
          </div>
        </div>

        <div className="hotspot-stat">
          <div className="hotspot-stat-label">
            <TrendingUp size={14} />
            MULTIPLE INDICATORS
          </div>

          <div className="hotspot-stat-value">
            {formatNumber(
              multipleIndicatorCount,
            )}
          </div>

          <div className="hotspot-stat-detail">
            Multiple high-risk indicators present
          </div>
        </div>

        <div className="hotspot-stat">
          <div className="hotspot-stat-label">
            <Gauge size={14} />
            SINGLE INDICATOR
          </div>

          <div className="hotspot-stat-value">
            {formatNumber(
              singleIndicatorCount,
            )}
          </div>

          <div className="hotspot-stat-detail">
            One high-risk indicator present
          </div>
        </div>

        <div className="hotspot-stat">
          <div className="hotspot-stat-label">
            <Database size={14} />
            ACCIDENT RECORDS
          </div>

          <div className="hotspot-stat-value">
            {formatNumber(
              totalAccidentsInsideHotspots,
            )}
          </div>

          <div className="hotspot-stat-detail">
            Records represented across candidates
          </div>
        </div>
      </section>

      <section className="hotspot-controls">
        <div className="hotspot-control-left">
          <select
            className="hotspot-select"
            value={selectedCity}
              onChange={(event) => { setSelectedCity(event.target.value); setAnalysisContext((current) => ({ ...current, city: event.target.value })); }}
          >
            <option>
              All Cities
            </option>

            {cities.map((city) => (
              <option
                key={city}
                value={city}
              >
                {city}
              </option>
            ))}
          </select>

          <select
            className="hotspot-select"
            value={selectedProfile}
            onChange={(event) =>
              setSelectedProfile(
                event.target.value,
              )
            }
          >
            <option>
              All Profiles
            </option>

            {profiles.map(
              (profile) => (
                <option
                  key={profile}
                  value={profile}
                >
                  {formatRiskProfile(
                    profile,
                  )}
                </option>
              ),
            )}
          </select>

          <select
            className="hotspot-select"
            value={minimumAccidents}
            onChange={(event) =>
              setMinimumAccidents(
                event.target.value,
              )
            }
          >
            <option value="0">
              Any accidents
            </option>

            <option value="15">
              15+ accidents
            </option>

            <option value="50">
              50+ accidents
            </option>

            <option value="100">
              100+ accidents
            </option>

            <option value="150">
              150+ accidents
            </option>

            <option value="200">
              200+ accidents
            </option>
          </select>
        </div>

        <div className="hotspot-search-wrap">
          <Search size={15} />

          <input
            className="hotspot-search"
            value={searchTerm}
            onChange={(event) =>
              setSearchTerm(
                event.target.value,
              )
            }
            placeholder="Search city or cluster..."
          />
        </div>

        <span className="results-count">
          {formatNumber(
            filteredHotspots.length,
          )}{" "}
          RESULTS
        </span>
      </section>

      <section className="hotspot-main-grid">
        <div className="panel hotspot-table-panel">
          <SectionHeader
            kicker="SPATIAL CLUSTER ANALYSIS"
            title="Hotspot candidates"
            meta="DBSCAN-derived"
          />

          {filteredHotspots.length === 0 ? (
            <EmptyState
              icon={Search}
              title="No matching hotspots"
              description="Try relaxing the filters or search term."
            />
          ) : (
            <div className="hotspot-table-wrap">
              <div className="hotspot-table-head">
                <span>LOCATION</span>
                <span>ACCIDENTS</span>
                <span>CASUALTIES</span>
                <span>FATAL</span>
                <span>MEAN RISK</span>
                <span>RISK PROFILE</span>
                <span />
              </div>

              {filteredHotspots.map(
                (hotspot) => {
                  const stats =
                    hotspot.statistics ||
                    {};

                  const isSelected =
                    selectedHotspot ===
                    hotspot;

                  return (
                    <button
                      type="button"
                      className={`hotspot-table-row ${
                        isSelected
                          ? "selected"
                          : ""
                      }`}
                      key={`${hotspot.city}-${hotspot.cluster_id}`}
                      onClick={() =>
                        setSelectedHotspot(
                          hotspot,
                        )
                      }
                    >
                      <div className="hotspot-location-cell">
                        <strong>
                          {hotspot.city}
                        </strong>

                        <span>
                          CLUSTER{" "}
                          {hotspot.cluster_id}
                        </span>
                      </div>

                      <span>
                        {formatNumber(
                          stats.accident_count,
                        )}
                      </span>

                      <span>
                        {formatNumber(
                          stats.total_casualties,
                        )}
                      </span>

                      <span>
                        {formatNumber(
                          stats.fatal_accidents,
                        )}
                      </span>

                      <span>
                        {formatDecimal(
                          stats.mean_risk_score,
                        )}
                      </span>

                      <div>
                        <span className="risk-profile-badge">
                          {formatRiskProfile(
                            hotspot.risk_profile,
                          )}
                        </span>

                        <div className="indicator-dots">
                          {[
                            "high_accident_density",
                            "high_fatality_proportion",
                            "high_casualty_burden",
                            "high_mean_risk_score",
                          ].map(
                            (key) => (
                              <span
                                key={key}
                                className={
                                  hotspot
                                    .risk_indicators?.[
                                    key
                                  ]
                                    ? "active"
                                    : ""
                                }
                              />
                            ),
                          )}
                        </div>
                      </div>

                      <ChevronRight
                        size={15}
                      />
                    </button>
                  );
                },
              )}
            </div>
          )}
        </div>

        <aside className="panel hotspot-detail-panel">
          {!selectedHotspot ? (
            <div className="hotspot-detail-empty">
              <div className="detail-empty-icon">
                <Target size={20} />
              </div>

              <strong>
                Select a hotspot candidate
              </strong>

              <p>
                Detailed spatial and risk indicators
                will appear here.
              </p>
            </div>
          ) : (
            <>
              <div className="hotspot-detail-top">
                <div>
                  <span className="panel-kicker">
                    SELECTED HOTSPOT
                  </span>

                  <h3>
                    {selectedHotspot.city}
                  </h3>

                  <span className="detail-cluster">
                    DBSCAN CLUSTER{" "}
                    {selectedHotspot.cluster_id}
                  </span>
                </div>

                <span className="risk-profile-badge">
                  {formatRiskProfile(
                    selectedHotspot.risk_profile,
                  )}
                </span>
              </div>

              <button
                type="button"
                className="map-action-button"
                onClick={() =>
                  openOnMap(
                    selectedHotspot,
                  )
                }
              >
                <MapPin size={15} />
                View on map
              </button>

              <div className="detail-section">
                <span className="panel-kicker">
                  ACCIDENT STATISTICS
                </span>

                <div className="detail-metric-grid">
                  <div>
                    <span>Accidents</span>
                    <strong>
                      {formatNumber(
                        selectedStats.accident_count,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Casualties</span>
                    <strong>
                      {formatNumber(
                        selectedStats.total_casualties,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Mean casualties</span>
                    <strong>
                      {formatDecimal(
                        selectedStats.mean_casualties,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Mean vehicles</span>
                    <strong>
                      {formatDecimal(
                        selectedStats.mean_vehicles,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Mean risk</span>
                    <strong>
                      {formatDecimal(
                        selectedStats.mean_risk_score,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Fatal</span>
                    <strong>
                      {formatNumber(
                        selectedStats.fatal_accidents,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Major</span>
                    <strong>
                      {formatNumber(
                        selectedStats.major_accidents,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Minor</span>
                    <strong>
                      {formatNumber(
                        selectedStats.minor_accidents,
                      )}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <span className="panel-kicker">
                  RISK INDICATORS
                </span>

                <div className="indicator-list">
                  <IndicatorRow
                    label="High accident density"
                    active={
                      selectedIndicators.high_accident_density
                    }
                  />

                  <IndicatorRow
                    label="High fatality proportion"
                    active={
                      selectedIndicators.high_fatality_proportion
                    }
                  />

                  <IndicatorRow
                    label="High casualty burden"
                    active={
                      selectedIndicators.high_casualty_burden
                    }
                  />

                  <IndicatorRow
                    label="High mean risk score"
                    active={
                      selectedIndicators.high_mean_risk_score
                    }
                  />
                </div>
              </div>

              <div className="detail-section">
                <span className="panel-kicker">
                  SEVERITY PROFILE
                </span>

                <div className="detail-metric-grid">
                  <div>
                    <span>Fatality proportion</span>
                    <strong>
                      {formatPercent(
                        selectedSeverity.fatal_proportion,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Major proportion</span>
                    <strong>
                      {formatPercent(
                        selectedSeverity.major_proportion,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Severe proportion</span>
                    <strong>
                      {formatPercent(
                        selectedSeverity.severe_proportion,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Mapping priority</span>
                    <strong>
                      {selectedHotspot.priority_for_mapping
                        ? "Priority"
                        : "Standard"}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <span className="panel-kicker">
                  LOCATION
                </span>

                <div className="coordinates">
                  <span>
                    Latitude{" "}
                    <b>
                      {formatDecimal(
                        selectedHotspot
                          .location?.latitude,
                        6,
                      )}
                    </b>
                  </span>

                  <span>
                    Longitude{" "}
                    <b>
                      {formatDecimal(
                        selectedHotspot
                          .location?.longitude,
                        6,
                      )}
                    </b>
                  </span>
                </div>
              </div>
            </>
          )}
        </aside>
      </section>
    </div>
  );
}

function IndicatorRow({
  label,
  active,
}) {
  return (
    <div className="indicator-row">
      <span
        className={`indicator-status ${
          active ? "active" : ""
        }`}
      >
        {active ? (
          <CheckCircle2 size={14} />
        ) : (
          <CircleDot size={14} />
        )}
      </span>

      <span>{label}</span>

      <b>
        {active
          ? "Detected"
          : "Not flagged"}
      </b>
    </div>
  );
}

/* =========================================================
   CITIES
   ========================================================= */

function Cities() {
  const { analysisContext, setAnalysisContext } = useAnalysisContext();
  const location = useLocation();
  const [dashboard, setDashboard] =
    useState(null);

  const [hotspots, setHotspots] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [selectedCity, setSelectedCity] = useState(analysisContext.city);

  const [comparisonCities, setComparisonCities] = useState(() => {
    const initial = new URLSearchParams(window.location.search).get("compare")?.split(",").filter((city) => ANALYSIS_CITIES.includes(city));
    return initial?.length ? initial.slice(0, 3) : ["Bangalore", "Delhi"];
  });
  const [comparisonData, setComparisonData] = useState([]);
  const [contextStats, setContextStats] = useState(null);

  async function loadCities() {
    try {
      setLoading(true);
      setError("");

      const [
        dashboardResponse,
        hotspotsResponse,
        contextResponse,
      ] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard`),
        fetch(`${API_BASE}/api/hotspots?${contextQuery(analysisContext)}`),
        fetch(`${API_BASE}/api/analysis/context?${contextQuery(analysisContext)}`),
      ]);

      if (!dashboardResponse.ok) {
        throw new Error(
          "Dashboard request failed.",
        );
      }

      if (!hotspotsResponse.ok) {
        throw new Error(
          "Hotspots request failed.",
        );
      }

      setDashboard(
        await dashboardResponse.json(),
      );

      const hotspotData =
        await hotspotsResponse.json();
      const scopedData = await contextResponse.json();
      setContextStats(scopedData);

      setHotspots(
        Array.isArray(
          hotspotData.hotspots,
        )
          ? hotspotData.hotspots
          : [],
      );
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Unable to load city intelligence.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCities();
  }, [analysisContext.city, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);

  useEffect(() => {
    if (analysisContext.city !== "All Cities") setSelectedCity(analysisContext.city);
  }, [analysisContext.city]);

  useEffect(() => {
    const requested = new URLSearchParams(location.search).get("compare")?.split(",").filter((city) => ANALYSIS_CITIES.includes(city));
    if (requested?.length) setComparisonCities(requested.slice(0, 3));
  }, [location.search]);

  useEffect(() => {
    Promise.all(comparisonCities.map(async (city) => {
      const scopedContext = { ...analysisContext, city };
      const [response, hotspotResponse] = await Promise.all([
        fetch(`${API_BASE}/api/analysis/context?${contextQuery(scopedContext)}`),
        fetch(`${API_BASE}/api/hotspots?${contextQuery(scopedContext)}`),
      ]);
      if (!response.ok || !hotspotResponse.ok) return null;
      const [data, hotspotData] = await Promise.all([response.json(), hotspotResponse.json()]);
      const cityData = data.cities?.[0] || { city, accidents: 0, clustered_records: 0, spatial_clusters: 0, casualties: 0 };
      return { ...cityData, hotspot_candidates: hotspotData.hotspots?.length || 0, multiple_indicators: hotspotData.hotspots?.filter((item) => item.risk_profile === "multiple_high_risk_indicators").length || 0 };
    })).then((rows) => setComparisonData(rows.filter(Boolean))).catch(console.error);
  }, [comparisonCities, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);

  const cities = Array.isArray(contextStats?.cities)
    ? contextStats.cities
    : Array.isArray(dashboard?.cities)
    ? dashboard.cities
    : [];

  const enrichedCities = useMemo(
    () =>
      cities.map((city) => {
        const cityHotspots =
          hotspots.filter(
            (hotspot) =>
              hotspot.city ===
              city.city,
          );

        const multiple =
          cityHotspots.filter(
            (hotspot) =>
              hotspot.risk_profile ===
              "multiple_high_risk_indicators",
          ).length;

        return {
          ...city,
          hotspot_candidates:
            cityHotspots.length,
          multiple_indicators:
            multiple,
        };
      }),
    [cities, hotspots],
  );

  const visibleCities =
    selectedCity === "All Cities"
      ? enrichedCities
      : enrichedCities.filter(
          (city) =>
            city.city ===
            selectedCity,
        );

  const totalAccidents =
    enrichedCities.reduce(
      (sum, city) =>
        sum +
        safeNumber(city.accidents),
      0,
    );

  const totalClustered =
    enrichedCities.reduce(
      (sum, city) =>
        sum +
        safeNumber(
          city.clustered_records,
        ),
      0,
    );

  if (loading) {
    return (
      <LoadingState label="Loading city intelligence..." />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="City intelligence unavailable"
        message={error}
        onRetry={loadCities}
      />
    );
  }

  return (
    <div className="data-page">
      <section className="stats-grid">
        <StatCard
          icon={Building2}
          label="ANALYSED CITIES"
          value={formatNumber(contextStats?.cities?.length ?? enrichedCities.length)}
          detail="Cities represented in the contemporary dataset"
          accent
        />

        <StatCard
          icon={AlertTriangle}
          label="ACCIDENT RECORDS"
          value={formatNumber(contextStats?.summary?.accidents ?? totalAccidents)}
          detail="Records in current global context"
        />

        <StatCard
          icon={Layers3}
          label="CLUSTERED RECORDS"
          value={formatNumber(contextStats?.summary?.clustered_records ?? totalClustered)}
          detail="Context records already assigned to DBSCAN clusters"
        />

        <StatCard
          icon={Target}
          label="HOTSPOT CANDIDATES"
          value={formatNumber(
            hotspots.length,
          )}
          detail="Across the seven clustered cities"
        />
      </section>

      <section className="panel">
        <div className="page-filter-bar">
          <div>
            <span className="panel-kicker">
              CITY COMPARISON
            </span>

            <h3>
              City intelligence
            </h3>
          </div>

          <select
            className="hotspot-select"
            value={selectedCity}
            onChange={(event) => { setSelectedCity(event.target.value); setAnalysisContext((current) => ({ ...current, city: event.target.value })); }}
          >
            <option>
              All Cities
            </option>

            {enrichedCities.map(
              (city) => (
                <option
                  key={city.city}
                  value={city.city}
                >
                  {city.city}
                </option>
              ),
            )}
          </select>
        </div>

        <div className="city-compare-tools">
          <div><span className="panel-kicker">COMPARE 2–3 CITIES</span><p>Select cities to compare in the current severity and date context.</p></div>
          <div className="city-compare-selectors">{ANALYSIS_CITIES.map((city) => <label key={city}><input type="checkbox" checked={comparisonCities.includes(city)} disabled={!comparisonCities.includes(city) && comparisonCities.length >= 3} onChange={() => setComparisonCities((current) => current.includes(city) ? current.filter((item) => item !== city) : [...current, city])} /><span>{city}</span></label>)}</div>
        </div>
        <div className="city-comparison-table">
          <div className="city-comparison-head"><span>MEASURE</span>{comparisonData.map((city) => <strong key={city.city}>{city.city}</strong>)}</div>
          {[{ label: "Accident records", key: "accidents" }, { label: "Clustered records", key: "clustered_records" }, { label: "Spatial clusters", key: "spatial_clusters" }, { label: "Hotspot candidates", key: "hotspot_candidates" }, { label: "Multi-indicator hotspots", key: "multiple_indicators" }, { label: "Casualties", key: "casualties" }].map((metric) => <div className="city-comparison-row" key={metric.key}><span>{metric.label}</span>{comparisonData.map((city) => <b key={city.city}>{formatNumber(city[metric.key])}</b>)}</div>)}
          <div className="city-comparison-bars">{comparisonData.map((city) => { const max = Math.max(1, ...comparisonData.map((item) => item.accidents)); return <div key={city.city}><span>{city.city}<b>{formatNumber(city.accidents)}</b></span><i><em style={{ width: `${city.accidents / max * 100}%` }} /></i></div>; })}</div>
        </div>

        <div className="city-intelligence-grid">
          {visibleCities.map(
            (city) => {
              const clusteringRate =
                safeNumber(
                  city.accidents,
                ) > 0
                  ? safeNumber(
                      city.clustered_records,
                    ) /
                    safeNumber(
                      city.accidents,
                    )
                  : 0;

              return (
                <div
                  className="city-intelligence-card"
                  key={city.city}
                >
                  <div className="city-card-top">
                    <div>
                      <span className="panel-kicker">
                        CITY
                      </span>

                      <h3>
                        {city.city}
                      </h3>
                    </div>

                    <span className="city-status">
                      <span className="status-dot" />
                      {city.city === "Chandigarh" ? "Descriptive only" : "Clustered"}
                    </span>
                  </div>

                  <div className="city-card-metrics">
                    <div>
                      <span>
                        Accidents
                      </span>

                      <strong>
                        {formatNumber(
                          city.accidents,
                        )}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Clustered
                      </span>

                      <strong>
                        {formatNumber(
                          city.clustered_records,
                        )}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Hotspots
                      </span>

                      <strong>
                        {formatNumber(
                          city.hotspot_candidates,
                        )}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Multi-indicator
                      </span>

                      <strong>
                        {formatNumber(
                          city.multiple_indicators,
                        )}
                      </strong>
                    </div>
                  </div>

                  <div className="city-progress">
                    <div className="city-progress-label">
                      <span>
                        Clustered record share
                      </span>

                      <b>
                        {formatPercent(
                          clusteringRate,
                        )}
                      </b>
                    </div>

                    <div className="city-progress-track">
                      <span
                        style={{
                          width: `${Math.min(
                            clusteringRate *
                              100,
                            100,
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            },
          )}
        </div>
      </section>

      <section className="panel">
        <SectionHeader
          kicker="CITY TABLE"
          title="Analytical coverage"
          meta="Descriptive comparison"
        />

        <div className="wide-data-table">
          <div className="wide-data-head">
            <span>CITY</span>
            <span>ACCIDENTS</span>
            <span>CLUSTERED</span>
            <span>CLUSTER SHARE</span>
            <span>HOTSPOTS</span>
            <span>MULTI-INDICATOR</span>
          </div>

          {enrichedCities
            .slice()
            .sort(
              (a, b) =>
                safeNumber(
                  b.accidents,
                ) -
                safeNumber(
                  a.accidents,
                ),
            )
            .map((city) => {
              const rate =
                safeNumber(
                  city.accidents,
                ) > 0
                  ? safeNumber(
                      city.clustered_records,
                    ) /
                    safeNumber(
                      city.accidents,
                    )
                  : 0;

              return (
                <div
                  className="wide-data-row"
                  key={city.city}
                >
                  <strong>
                    {city.city}
                  </strong>

                  <span>
                    {formatNumber(
                      city.accidents,
                    )}
                  </span>

                  <span>
                    {formatNumber(
                      city.clustered_records,
                    )}
                  </span>

                  <span>
                    {formatPercent(
                      rate,
                    )}
                  </span>

                  <span>
                    {formatNumber(
                      city.hotspot_candidates,
                    )}
                  </span>

                  <span>
                    {formatNumber(
                      city.multiple_indicators,
                    )}
                  </span>
                </div>
              );
            })}
        </div>
      </section>
    </div>
  );
}

/* =========================================================
   RISK FACTORS
   ========================================================= */

function RiskFactors() {
  const { analysisContext } = useAnalysisContext();
  const [factorData, setFactorData] =
    useState(null);

  const [roadTypeData, setRoadTypeData] =
    useState(null);

  const [numericData, setNumericData] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  async function loadFactors() {
    try {
      setLoading(true);
      setError("");

      const factorResponse = await fetch(`${API_BASE}/api/analysis/context?${contextQuery(analysisContext)}`);

      if (!factorResponse.ok) {
        throw new Error(
          "Factors API request failed.",
        );
      }

      const factorJson = await factorResponse.json();
      setFactorData(factorJson?.factors ?? {});
      setRoadTypeData(factorJson?.factors?.road_type ?? []);
      setNumericData({ records: factorJson?.summary?.clustered_records, summary: factorJson?.numeric });
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Unable to load risk-factor intelligence.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFactors();
  }, [analysisContext.city, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);

  const factorObject = factorData || {};
  const factorEntries = Object.entries(factorObject)
    .map(([name, rows]) => [name, rows]);
  const roadRows = (roadTypeData || []).map((row) => ({
    road_type: row.value,
    records: row.count,
    share: row.percent,
  }));
  const numericRows = Object.entries(numericData?.summary || {}).map(
    ([factor, summary]) => ({ factor, ...summary }),
  );

  if (loading) {
    return (
      <LoadingState label="Loading risk-factor intelligence..." />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Risk-factor intelligence unavailable"
        message={error}
        onRetry={loadFactors}
      />
    );
  }

  return (
    <div className="data-page">
      <section className="stats-grid">
        <StatCard
          icon={BarChart3}
          label="FACTOR SIGNALS"
          value={formatNumber(
            factorEntries.length,
          )}
          detail="Factor values exposed by the analysis API"
          accent
        />

        <StatCard
          icon={Layers3}
          label="ROAD TYPE ROWS"
          value={formatNumber(
            roadRows.length,
          )}
          detail="Road-type analytical records"
        />

        <StatCard
          icon={Gauge}
          label="NUMERIC FACTORS"
          value={formatNumber(
            numericRows.length,
          )}
          detail="Numeric factor summaries"
        />

        <StatCard
          icon={Shield}
          label="INTERPRETATION"
          value="DESCRIPTIVE"
          detail="Observed patterns are not causal claims"
        />
      </section>

      <section className="factor-layout">
        <div className="panel">
          <SectionHeader
            kicker="FACTOR SUMMARY"
            title="Observed factor signals"
            meta="API-derived"
          />

          {factorEntries.length === 0 ? (
            <EmptyState
              icon={BarChart3}
              title="No summary rows available"
              description="The factors endpoint returned no simple summary values."
            />
          ) : (
            <div className="factor-list">
              {factorEntries.map(
                ([key, value]) => (
                  <div
                    className="factor-row"
                    key={key}
                  >
                    <div><strong>{humanize(key)}</strong><span>Current context distribution</span></div>
                    <div className="factor-value-tags">{value.slice(0, 3).map((item) => <span key={item.value}>{humanize(item.value)} <b>{formatDecimal(item.percent)}%</b></span>)}</div>
                  </div>
                ),
              )}
            </div>
          )}
        </div>

        <div className="panel">
          <SectionHeader
            kicker="ROAD ENVIRONMENT"
            title="Road-type analysis"
            meta={`${roadRows.length} rows`}
          />

          {roadRows.length === 0 ? (
            <EmptyState
              icon={MapIcon}
              title="No road-type rows"
              description="The road-type endpoint did not return tabular data."
            />
          ) : (
            <div className="factor-table">
              {roadRows
                .slice(0, 12)
                .map(
                  (row, index) => {
                    const entries =
                      Object.entries(
                        row || {},
                      );

                    const label =
                      row.road_type ??
                      row.type ??
                      row.name ??
                      entries[0]?.[1] ??
                      `Row ${index + 1}`;

                    const values =
                      entries
                        .filter(
                          ([key]) =>
                            key !==
                            "road_type" &&
                            key !==
                            "type" &&
                            key !==
                            "name",
                        )
                        .slice(0, 3);

                    return (
                      <div
                        className="factor-table-row"
                        key={`${label}-${index}`}
                      >
                        <strong>
                          {humanize(
                            label,
                          )}
                        </strong>

                        <div>
                          {values.map(
                            ([key, value]) => (
                              <span
                                key={key}
                              >
                                {humanize(
                                  key,
                                )}:{" "}
                                <b>
                                  {typeof value ===
                                  "number"
                                    ? formatDecimal(
                                        value,
                                      )
                                    : humanize(
                                        value,
                                      )}
                                </b>
                              </span>
                            ),
                          )}
                        </div>
                      </div>
                    );
                  },
                )}
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <SectionHeader
          kicker="NUMERIC FACTORS"
          title="Numeric factor signals"
          meta={`${numericRows.length} rows`}
        />

        {numericRows.length === 0 ? (
          <EmptyState
            icon={Gauge}
            title="No numeric factor rows"
            description="The numeric-factor endpoint did not return tabular data."
          />
        ) : (
          <div className="wide-data-table">
            {numericRows
              .slice(0, 20)
              .map((row, index) => {
                const entries =
                  Object.entries(
                    row || {},
                  );

                return (
                  <div
                    className="wide-data-row factor-wide-row"
                    key={index}
                  >
                    {entries
                      .slice(0, 6)
                      .map(
                        ([key, value]) => (
                          <span
                            key={key}
                          >
                            <small>
                              {humanize(
                                key,
                              )}
                            </small>

                            <b>
                              {typeof value ===
                              "number"
                                ? formatDecimal(
                                    value,
                                  )
                                : humanize(
                                    value,
                                  )}
                            </b>
                          </span>
                        ),
                      )}
                  </div>
                );
              })}
          </div>
        )}
      </section>

      <div className="analysis-note">
        <Shield size={17} />

        <div>
          <strong>
            Interpretation note
          </strong>

          <p>
            Risk-factor views describe distributions and
            associations present in the supplied data. They
            should not be interpreted as evidence that a
            single factor causes accidents.
          </p>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   HISTORY
   ========================================================= */

function HistoricalHistory() {
  const [data, setData] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [search, setSearch] =
    useState("");

  const [district, setDistrict] =
    useState("All Districts");

  async function loadHistory() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE}/api/history/kerala`,
      );

      if (!response.ok) {
        throw new Error(
          "Historical API request failed.",
        );
      }

      setData(
        await response.json(),
      );
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Unable to load Kerala historical intelligence.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  const records = Array.isArray(
    data?.records,
  )
    ? data.records
    : [];

  const districts = useMemo(
    () =>
      Array.from(
        new Set(
          records
            .map(
              (record) =>
                record.district,
            )
            .filter(Boolean),
        ),
      ).sort(),
    [records],
  );

  const filteredRecords =
    records.filter(
      (record) => {
        const districtMatch =
          district ===
            "All Districts" ||
          record.district ===
            district;

        const query =
          search
            .trim()
            .toLowerCase();

        const searchable = [
          record.location,
          record.district,
          record.police_station,
          record.road_name,
          record.road_number,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return (
          districtMatch &&
          (!query ||
            searchable.includes(
              query,
            ))
        );
      },
    );

  if (loading) {
    return (
      <LoadingState label="Loading Kerala historical data..." />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Historical data unavailable"
        message={error}
        onRetry={loadHistory}
      />
    );
  }

  return (
    <div className="data-page">
      <section className="stats-grid">
        <StatCard
          icon={HistoryIcon}
          label="SOURCE RECORDS"
          value={formatNumber(
            data?.summary?.total,
          )}
          detail="Rows represented by the historical source"
          accent
        />

        <StatCard
          icon={MapPin}
          label="MAPPED RECORDS"
          value={formatNumber(
            data?.summary?.mapped,
          )}
          detail="Records with complete start and end coordinates"
        />

        <StatCard
          icon={CircleDot}
          label="UNMAPPED RECORDS"
          value={formatNumber(
            data?.summary?.unmapped,
          )}
          detail="Records missing one or more endpoint coordinates"
        />

        <StatCard
          icon={Shield}
          label="DATA TYPE"
          value="HISTORICAL"
          detail="Separate Kerala reference layer"
        />
      </section>

      <section className="panel">
        <div className="page-filter-bar">
          <div>
            <span className="panel-kicker">
              KERALA BLACK SPOTS
            </span>

            <h3>
              Historical reference records
            </h3>
          </div>

          <div className="filter-group">
            <select
              className="hotspot-select"
              value={district}
              onChange={(event) =>
                setDistrict(
                  event.target.value,
                )
              }
            >
              <option>
                All Districts
              </option>

              {districts.map(
                (item) => (
                  <option
                    key={item}
                    value={item}
                  >
                    {item}
                  </option>
                ),
              )}
            </select>

            <div className="hotspot-search-wrap">
              <Search size={15} />

              <input
                className="hotspot-search"
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value,
                  )
                }
                placeholder="Search location, road..."
              />
            </div>
          </div>
        </div>

        {filteredRecords.length ===
        0 ? (
          <EmptyState
            icon={Search}
            title="No historical records match"
            description="Try another district or search term."
          />
        ) : (
          <div className="wide-data-table">
            <div className="wide-data-head history-head">
              <span>LOCATION</span>
              <span>DISTRICT</span>
              <span>POLICE STATION</span>
              <span>ROAD</span>
              <span>COORDINATES</span>
            </div>

            {filteredRecords
              .slice(0, 100)
              .map(
                (record, index) => (
                  <div
                    className="wide-data-row history-row"
                    key={`${record.sl_no}-${index}`}
                  >
                    <strong>
                      {record.location ||
                        "Unnamed location"}
                    </strong>

                    <span>
                      {record.district ||
                        "—"}
                    </span>

                    <span>
                      {record.police_station ||
                        "—"}
                    </span>

                    <span>
                      {record.road_name ||
                        "—"}
                    </span>

                    <span>
                      {record.start
                        ?.latitude !==
                      undefined
                        ? `${formatDecimal(
                            record.start.latitude,
                            5,
                          )}, ${formatDecimal(
                            record.start.longitude,
                            5,
                          )}`
                        : "Unmapped"}
                    </span>
                  </div>
                ),
              )}
          </div>
        )}

        {filteredRecords.length >
          100 && (
          <div className="table-footer-note">
            Showing the first 100 matching historical
            records.
          </div>
        )}
      </section>

      <div className="analysis-note">
        <HistoryIcon size={17} />

        <div>
          <strong>
            Historical layer kept separate
          </strong>

          <p>
            This dataset is a historical Kerala black-spot
            reference and is not merged into the contemporary
            eight-city accident dataset.
          </p>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   ROAD SAFETY LAB
   ========================================================= */

function RoadSafetyLab() {
  const navigate = useNavigate();
  const { analysisContext, setAnalysisContext } = useAnalysisContext();
  const [hotspots, setHotspots] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [minimumAccidents, setMinimumAccidents] =
    useState(15);
  const [selectedProfile, setSelectedProfile] = useState("All Profiles");

  useEffect(() => {
    let cancelled = false;

    async function loadLab() {
      try {
        setLoading(true);

        const response = await fetch(
          `${API_BASE}/api/hotspots?${contextQuery(analysisContext)}`,
        );

        if (!response.ok) {
          throw new Error(
            "Lab hotspot request failed.",
          );
        }

        const data =
          await response.json();

        if (!cancelled) {
          setHotspots(
            Array.isArray(
              data.hotspots,
            )
              ? data.hotspots
              : [],
          );
        }
      } catch (error) {
        console.error(error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadLab();

    return () => {
      cancelled = true;
    };
  }, [analysisContext.city, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);




  const filtered = useMemo(
    () =>
      hotspots.filter(
        (hotspot) =>
          (analysisContext.city ===
            "All Cities" ||
            hotspot.city ===
              analysisContext.city) &&
          (selectedProfile === "All Profiles" || hotspot.risk_profile === selectedProfile) &&
          (analysisContext.severity === "All Severities" || safeNumber(hotspot.statistics?.[`${analysisContext.severity}_accidents`]) > 0) &&
          safeNumber(
            hotspot.statistics
              ?.accident_count,
          ) >=
            minimumAccidents,
      ),
    [
      hotspots,
      analysisContext.city,
      analysisContext.severity,
      selectedProfile,
      minimumAccidents,
    ],
  );

  const profileCounts =
    useMemo(() => {
      const counts = {};

      filtered.forEach(
        (hotspot) => {
          const profile =
            hotspot.risk_profile ||
            "unclassified";

          counts[profile] =
            (counts[profile] || 0) +
            1;
        },
      );

      return Object.entries(
        counts,
      ).sort(
        (a, b) =>
          b[1] - a[1],
      );
    }, [filtered]);

  const largestHotspots =
    [...filtered]
      .sort(
        (a, b) =>
          safeNumber(
            b.statistics
              ?.accident_count,
          ) -
          safeNumber(
            a.statistics
              ?.accident_count,
          ),
      )
      .slice(0, 8);

  function locateLabHotspot(hotspot) {
    setAnalysisContext((current) => ({ ...current, city: hotspot.city }));
    navigate(`/map?city=${encodeURIComponent(hotspot.city)}&cluster=${hotspot.cluster_id}`, {
      state: { focus: { latitude: hotspot.location?.latitude, longitude: hotspot.location?.longitude } },
    });
  }

  if (loading) {
    return (
      <LoadingState label="Loading Road Safety Lab..." />
    );
  }

  return (
    <div className="data-page">
      <section className="lab-control-panel">
        <div>
          <span className="panel-kicker">
            EXPLORATION CONTROLS
          </span>

          <h3>
            Adjust the hotspot view
          </h3>

          <p>
            Context filters narrow records within existing hotspot candidates; DBSCAN cluster identities and full-period risk profiles remain unchanged.
          </p>
        </div>

        <div className="lab-controls">
          <select
            className="hotspot-select"
            value={analysisContext.city}
            onChange={(event) =>
              setAnalysisContext((current) => ({ ...current, city: event.target.value }))
            }
          >
            <option>
              All Cities
            </option>

            {ANALYSIS_CITIES.map(
              (city) => (
                <option
                  key={city}
                  value={city}
                >
                  {city}
                </option>
              ),
            )}
          </select>

          <select className="hotspot-select" value={selectedProfile} onChange={(event) => setSelectedProfile(event.target.value)}>
            <option value="All Profiles">All risk profiles</option>
            {[...new Set(hotspots.map((hotspot) => hotspot.risk_profile).filter(Boolean))].map((profile) => <option key={profile} value={profile}>{formatRiskProfile(profile)}</option>)}
          </select>

          <select className="hotspot-select" value={analysisContext.severity} onChange={(event) => setAnalysisContext((current) => ({ ...current, severity: event.target.value }))}>
            <option>All Severities</option><option value="fatal">Fatal present</option><option value="major">Major present</option><option value="minor">Minor present</option>
          </select>

          <label className="range-control">
            <span>
              Minimum accidents:{" "}
              <b>
                {minimumAccidents}
              </b>
            </span>

            <input
              type="range"
              min="15"
              max="200"
              step="5"
              value={minimumAccidents}
              onChange={(event) =>
                setMinimumAccidents(
                  Number(
                    event.target.value,
                  ),
                )
              }
            />
          </label>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          icon={Target}
          label="MATCHING HOTSPOTS"
          value={formatNumber(
            filtered.length,
          )}
          detail="Candidates meeting current lab filters"
          accent
        />

        <StatCard
          icon={Activity}
          label="ACCIDENT RECORDS"
          value={formatNumber(
            filtered.reduce(
              (sum, item) =>
                sum +
                safeNumber(
                  item.statistics
                    ?.accident_count,
                ),
              0,
            ),
          )}
          detail="Records represented by matching candidates"
        />

        <StatCard
          icon={TrendingUp}
          label="MULTI-INDICATOR"
          value={formatNumber(
            filtered.filter(
              (item) =>
                item.risk_profile ===
                "multiple_high_risk_indicators",
            ).length,
          )}
          detail="Multiple high-risk indicators"
        />

        <StatCard
          icon={Gauge}
          label="THRESHOLD"
          value={`${minimumAccidents}+`}
          detail="Minimum accidents per candidate"
        />
      </section>

      <section className="lab-grid">
        <div className="panel">
          <SectionHeader
            kicker="PROFILE DISTRIBUTION"
            title="Risk profiles in current view"
          />

          <div className="profile-bars">
            {profileCounts.map(
              ([profile, count]) => {
                const max =
                  profileCounts[0]?.[1] ||
                  1;

                return (
                  <button type="button"
                    className="profile-bar-row"
                    key={profile}
                    onClick={() => setSelectedProfile(profile)}
                  >
                    <div className="profile-bar-label">
                      <span>
                        {formatRiskProfile(
                          profile,
                        )}
                      </span>

                      <b>
                        {formatNumber(
                          count,
                        )}
                      </b>
                    </div>

                    <div className="profile-bar-track">
                      <span
                        style={{
                          width: `${(count / max) * 100}%`,
                        }}
                      />
                    </div>
                  </button>
                );
              },
            )}
          </div>
        </div>

        <div className="panel">
          <SectionHeader
            kicker="LARGEST CANDIDATES"
            title="Current hotspot set"
          />

          <div className="lab-hotspot-list">
            {largestHotspots.map(
              (hotspot) => (
                <div
                  className="lab-hotspot-item"
                  key={`${hotspot.city}-${hotspot.cluster_id}`}
                >
                  <div>
                    <strong>
                      {hotspot.city}
                    </strong>

                    <span>
                      Cluster{" "}
                      {
                        hotspot.cluster_id
                      }
                    </span>
                  </div>

                  <b>
                    {formatNumber(
                      hotspot.statistics
                        ?.accident_count,
                    )}
                  </b>
                  <button type="button" className="text-action" onClick={() => locateLabHotspot(hotspot)}>Locate on map</button>
                </div>
              ),
            )}
          </div>
        </div>
      </section>

      <div className="analysis-note">
        <FlaskConical size={17} />

        <div>
          <strong>
            Lab interpretation
          </strong>

          <p>
            The Road Safety Lab is an exploratory interface over
            the existing analysis outputs. It does not imply a
            causal ranking, prediction or new composite risk score.
          </p>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   REPORTS
   ========================================================= */

function Reports() {
  const { analysisContext } = useAnalysisContext();
  const [analysisData, setAnalysisData] = useState(null);
  const [dashboard, setDashboard] =
    useState(null);

  const [hotspots, setHotspots] =
    useState([]);

  const [history, setHistory] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  async function loadReports() {
    try {
      setLoading(true);
      setError("");

      const [
        dashboardResponse,
        hotspotsResponse,
        historyResponse,
        analysisResponse,
      ] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard`),
        fetch(`${API_BASE}/api/hotspots?${contextQuery(analysisContext)}`),
        fetch(
          `${API_BASE}/api/history/kerala`,
        ),
        fetch(`${API_BASE}/api/analysis/context?${contextQuery(analysisContext)}`),
      ]);

      if (!dashboardResponse.ok) {
        throw new Error(
          "Dashboard request failed.",
        );
      }

      if (!hotspotsResponse.ok) {
        throw new Error(
          "Hotspot request failed.",
        );
      }

      if (!historyResponse.ok) {
        throw new Error(
          "History request failed.",
        );
      }
      if (!analysisResponse.ok) throw new Error("Analysis context request failed.");

      const [dashboardData, analysisJson] = await Promise.all([dashboardResponse.json(), analysisResponse.json()]);
      setDashboard(dashboardData);
      setAnalysisData(analysisJson);

      const hotspotData =
        await hotspotsResponse.json();

      const historyData =
        await historyResponse.json();

      setHotspots(
        Array.isArray(
          hotspotData.hotspots,
        )
          ? hotspotData.hotspots
          : [],
      );

      setHistory(historyData);
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Unable to assemble the analytical report.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, [analysisContext.city, analysisContext.severity, analysisContext.startYear, analysisContext.endYear]);

  const cityRows =
    Array.isArray(
      analysisData?.cities,
    )
      ? analysisData.cities.map((city) => ({ ...city, hotspot_candidates: hotspots.filter((hotspot) => hotspot.city === city.city).length }))
      : [];
  const scopedHotspotCount = cityRows.reduce((sum, city) => sum + city.hotspot_candidates, 0);

  const topHotspots =
    [...hotspots]
      .sort(
        (a, b) =>
          safeNumber(
            b.statistics
              ?.accident_count,
          ) -
          safeNumber(
            a.statistics
              ?.accident_count,
          ),
      )
      .slice(0, 10);

  function downloadReport() {
    const lines = [
      "ROADSAFE INDIA — ANALYTICAL SUMMARY",
      "",
      `Scope: ${analysisContext.city} · ${humanize(analysisContext.severity)} · ${analysisContext.startYear}–${analysisContext.endYear}`,
      `Total accident records: ${analysisData?.summary?.accidents ?? "—"}`,
      `Spatial clusters in scope: ${analysisData?.summary?.spatial_clusters ?? "—"}`,
      `Hotspot candidates (city scope, full period): ${scopedHotspotCount}`,
      `Multiple-indicator hotspots: ${dashboard?.overview?.multiple_indicator_hotspots ?? "—"}`,
      "",
      "CITY COVERAGE",
      ...cityRows.map(
        (city) =>
          `${city.city}: ${city.accidents} accidents; ${city.clustered_records} clustered records`,
      ),
      "",
      "TOP HOTSPOT CANDIDATES",
      ...topHotspots.map(
        (hotspot) =>
          `${hotspot.city} — cluster ${hotspot.cluster_id}: ${hotspot.statistics?.accident_count ?? 0} accidents; ${formatRiskProfile(hotspot.risk_profile)}`,
      ),
      "",
      "HISTORICAL KERALA REFERENCE",
      `Source records: ${history?.summary?.total ?? "—"}`,
      `Mapped records: ${history?.summary?.mapped ?? "—"}`,
      `Unmapped records: ${history?.summary?.unmapped ?? "—"}`,
      "",
      "RoadSafe India combines a contemporary selected-city accident dataset with a separate historical Kerala black-spot reference layer.",
    ];

    const blob = new Blob(
      [lines.join("\n")],
      {
        type: "text/plain;charset=utf-8",
      },
    );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;
    link.download =
      "roadsafe-india-summary.txt";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <LoadingState label="Preparing analytical report..." />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Report data unavailable"
        message={error}
        onRetry={loadReports}
      />
    );
  }

  return (
    <div className="data-page">
      <section className="report-hero">
        <div>
          <span className="panel-kicker">
            ROADSAFE INDIA REPORT
          </span>

          <h2>
            Analytical intelligence summary
          </h2>

          <p>
            A concise view of the current dataset, spatial
            clustering outputs, hotspot candidates and the
            separate historical Kerala reference layer.
          </p>
        </div>

        <button
          type="button"
          className="primary-action"
          onClick={downloadReport}
        >
          <Download size={15} />
          Export summary
        </button>
      </section>

      <section className="stats-grid">
        <StatCard
          icon={AlertTriangle}
          label="ACCIDENT RECORDS"
          value={formatNumber(analysisData?.summary?.accidents)}
          detail="Current global analysis context"
        />

        <StatCard
          icon={Layers3}
          label="SPATIAL CLUSTERS"
          value={formatNumber(
            analysisData?.summary?.spatial_clusters,
          )}
          detail="Existing DBSCAN cluster records in scope"
          accent
        />

        <StatCard
          icon={Target}
          label="HOTSPOTS"
          value={formatNumber(
            scopedHotspotCount,
          )}
          detail="City scope; DBSCAN candidates are full-period"
        />

        <StatCard
          icon={HistoryIcon}
          label="KERALA RECORDS"
          value={formatNumber(
            history?.summary?.total,
          )}
          detail="Separate historical Kerala reference"
        />
      </section>

      <section className="report-grid">
        <div className="panel">
          <SectionHeader
            kicker="CITY COVERAGE"
            title="City summary"
          />

          <div className="report-city-list">
            {cityRows.map(
              (city) => (
                <div
                  className="report-city-row"
                  key={city.city}
                >
                  <strong>
                    {city.city}
                  </strong>

                  <span>
                    {formatNumber(
                      city.accidents,
                    )}{" "}
                    accidents
                  </span>

                  <span>
                    {formatNumber(
                      city.clustered_records,
                    )}{" "}
                    clustered
                  </span>

                  {city.city === "Chandigarh" && (
                    <span>Descriptive only</span>
                  )}
                </div>
              ),
            )}
          </div>
        </div>

        <div className="panel">
          <SectionHeader
            kicker="TOP CANDIDATES"
            title="Largest hotspot clusters"
          />

          <div className="report-hotspot-list">
            {topHotspots.map(
              (hotspot) => (
                <div
                  className="report-hotspot-row"
                  key={`${hotspot.city}-${hotspot.cluster_id}`}
                >
                  <div>
                    <strong>
                      {hotspot.city}
                    </strong>

                    <span>
                      Cluster{" "}
                      {
                        hotspot.cluster_id
                      }
                    </span>
                  </div>

                  <div>
                    <b>
                      {formatNumber(
                        hotspot
                          .statistics
                          ?.accident_count,
                      )}
                    </b>

                    <span>
                      accidents
                    </span>
                  </div>
                </div>
              ),
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <SectionHeader
          kicker="INTERPRETATION"
          title="How to read this report"
        />

        <div className="report-interpretation">
          <div>
            <CheckCircle2 size={17} />

            <p>
              Accident totals describe recorded observations
              in the contemporary dataset.
            </p>
          </div>

          <div>
            <CheckCircle2 size={17} />

            <p>
              DBSCAN clusters identify spatial concentration;
              they do not by themselves establish causation.
            </p>
          </div>

          <div>
            <CheckCircle2 size={17} />

            <p>
              Hotspot risk indicators are descriptive
              indicators and are not combined into an invented
              composite score.
            </p>
          </div>

          <div>
            <CheckCircle2 size={17} />

            <p>
              Historical Kerala records remain a separate
              reference dataset.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

/* =========================================================
   METHODOLOGY
   ========================================================= */

function Methodology() {
  return (
    <div className="data-page">
      <section className="methodology-hero">
        <div>
          <span className="panel-kicker">
            ROADSAFE INDIA
          </span>

          <h2>
            From raw records to spatial intelligence
          </h2>

          <p>
            The platform connects prepared accident data,
            spatial clustering and analytical views without
            introducing a separate database or invented risk
            model.
          </p>
        </div>

        <div className="methodology-badge">
          <Shield size={18} />
          Transparent analysis
        </div>
      </section>

      <section className="methodology-flow">
        <MethodStep
          number="01"
          icon={Database}
          title="Data preparation"
          description="The contemporary accident dataset is cleaned and prepared for analysis. Invalid spatial coordinates are excluded where required."
        />

        <MethodStep
          number="02"
          icon={MapPin}
          title="Spatial representation"
          description="Latitude and longitude are used to represent accident locations and support spatial exploration."
        />

        <MethodStep
          number="03"
          icon={Layers3}
          title="City-wise DBSCAN"
          description="DBSCAN is applied city by city using Haversine distance, with city-specific epsilon and minimum-sample configurations."
        />

        <MethodStep
          number="04"
          icon={Target}
          title="Hotspot candidates"
          description="Cluster-level candidate outputs are derived from accident-count and indicator criteria. Candidates are not treated as a universal risk score."
        />

        <MethodStep
          number="05"
          icon={BarChart3}
          title="Factor analysis"
          description="Road, environmental and numerical variables are examined descriptively to understand distributions around accident records."
        />

        <MethodStep
          number="06"
          icon={FileText}
          title="Decision views"
          description="The frontend exposes maps, city comparisons, hotspot exploration, factor views, historical reference and reports."
        />
      </section>

      <section className="methodology-grid">
        <div className="panel">
          <SectionHeader
            kicker="CONTEMPORARY DATASET"
            title="Scope"
          />

          <div className="methodology-list">
            <MethodologyRow
              label="Records"
              value="20,000 records"
            />

            <MethodologyRow
              label="Cities"
              value="8 selected cities"
            />

            <MethodologyRow
              label="Date range"
              value="2022-01-01 → 2025-04-15"
            />

            <MethodologyRow
              label="Severity classes"
              value="Minor / Major / Fatal"
            />
          </div>
        </div>

        <div className="panel">
          <SectionHeader
            kicker="SPATIAL ANALYSIS"
            title="DBSCAN output"
          />

          <div className="methodology-list">
            <MethodologyRow
              label="Distance"
              value="Haversine"
            />

            <MethodologyRow
              label="Parameterisation"
              value="City-specific"
            />

            <MethodologyRow
              label="Clusters"
              value="431 total"
            />

            <MethodologyRow
              label="Clustered records"
              value="14,151"
            />
          </div>
        </div>
      </section>

      <section className="panel">
        <SectionHeader
          kicker="IMPORTANT LIMITATIONS"
          title="Interpretation boundaries"
        />

        <div className="limitations-grid">
          <Limitation
            title="Selected-city scope"
            text="The contemporary dataset covers eight selected cities and should not be presented as a complete India-wide accident census."
          />

          <Limitation
            title="Historical separation"
            text="The Kerala historical black-spot dataset is a separate reference layer and is not treated as part of the contemporary city totals."
          />

          <Limitation
            title="Descriptive indicators"
            text="Risk indicators describe observed cluster characteristics and should not be interpreted as causal findings."
          />

          <Limitation
            title="Approximate map aids"
            text="Visual hotspot boundaries are presentation aids; they should not be interpreted as exact statistical DBSCAN polygons."
          />
        </div>
      </section>
    </div>
  );
}

function MethodStep({
  number,
  icon: Icon,
  title,
  description,
}) {
  return (
    <div className="method-step">
      <div className="method-step-number">
        {number}
      </div>

      <div className="method-step-icon">
        <Icon size={19} />
      </div>

      <div>
        <h3>{title}</h3>

        <p>{description}</p>
      </div>
    </div>
  );
}

function MethodologyRow({
  label,
  value,
}) {
  return (
    <div className="methodology-row">
      <span>{label}</span>

      <strong>{value}</strong>
    </div>
  );
}

function Limitation({
  title,
  text,
}) {
  return (
    <div className="limitation-card">
      <AlertTriangle size={17} />

      <div>
        <strong>{title}</strong>

        <p>{text}</p>
      </div>
    </div>
  );
}

/* =========================================================
   HEADER
   ========================================================= */

function PageHeader() {
  const location = useLocation();

  const meta =
    pageMeta[location.pathname] ||
    pageMeta["/"];

  return (
    <div className="page-header">
      <div>
        <span className="section-kicker">
          {meta.eyebrow}
        </span>

        <h1>
          {meta.title}
        </h1>

        <p>
          {meta.description}
        </p>
      </div>

      <div className="header-chip">
        <span className="status-dot" />
        ANALYSIS ACTIVE
      </div>
    </div>
  );
}

function CommandPalette({ onClose }) {
  const navigate = useNavigate();
  const { setAnalysisContext } = useAnalysisContext();
  const [query, setQuery] = useState("");
  const [hotspots, setHotspots] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
    fetch(`${API_BASE}/api/hotspots`).then((response) => response.json()).then((data) => setHotspots(data.hotspots || [])).catch(() => setHotspots([]));
  }, []);

  const pages = navigation.map((item) => ({ label: item.label, detail: "Open page", action: () => navigate(item.path) }));
  const cityOptions = ANALYSIS_CITIES.map((city) => ({
    label: `Set city: ${city}`, detail: "Update global analysis context", action: () => { setAnalysisContext((current) => ({ ...current, city })); navigate("/map"); },
  }));
  const hotspotOptions = hotspots.map((hotspot) => ({
    label: `${hotspot.city} · Cluster ${hotspot.cluster_id}`,
    detail: `${formatNumber(hotspot.statistics?.accident_count)} accidents · ${formatRiskProfile(hotspot.risk_profile)}`,
    action: () => { setAnalysisContext((current) => ({ ...current, city: hotspot.city })); navigate(`/hotspots?city=${encodeURIComponent(hotspot.city)}&cluster=${hotspot.cluster_id}`); },
  }));
  const compareMatch = query.match(/compare\s+([a-z]+)\s+(?:and|&)\s+([a-z]+)/i);
  const searchItems = [
    ...(compareMatch && ANALYSIS_CITIES.some((city) => city.toLowerCase() === compareMatch[1].toLowerCase()) && ANALYSIS_CITIES.some((city) => city.toLowerCase() === compareMatch[2].toLowerCase()) ? [{ label: `Compare ${compareMatch[1]} and ${compareMatch[2]}`, detail: "Open city comparison", action: () => { setAnalysisContext((current) => ({ ...current, city: "All Cities" })); navigate(`/cities?compare=${compareMatch[1]},${compareMatch[2]}`); } }] : []),
    ...(query.toLowerCase().includes("fatal") ? [{ label: "Show fatal accidents", detail: "Set global severity context", action: () => { setAnalysisContext((current) => ({ ...current, severity: "fatal" })); navigate("/map"); } }] : []),
    ...pages, ...cityOptions, ...hotspotOptions,
  ].filter((item) => !query || `${item.label} ${item.detail}`.toLowerCase().includes(query.toLowerCase())).slice(0, 12);

  return (
    <div className="command-palette-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="command-palette" role="dialog" aria-modal="true" aria-label="RoadSafe command palette">
        <div className="command-palette-input"><Search size={18} /><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && searchItems[0]) { searchItems[0].action(); onClose(); } }} placeholder="Search pages, cities, clusters, or commands…" /><kbd>ESC</kbd></div>
        <div className="command-palette-results">{searchItems.map((item) => <button type="button" key={`${item.label}-${item.detail}`} onClick={() => { item.action(); onClose(); }}><span><strong>{item.label}</strong><small>{item.detail}</small></span><ChevronRight size={15} /></button>)}{searchItems.length === 0 && <p>No matching pages, cities, or hotspots.</p>}</div>
        <footer><span>↑ ↓ navigate</span><span>Enter select</span><span>Esc close</span></footer>
      </section>
    </div>
  );
}

/* =========================================================
   TOPBAR
   ========================================================= */

function Topbar({
  setMobileOpen,
}) {
  const { analysisContext, setAnalysisContext, openCommandPalette } = useAnalysisContext();
  const location = useLocation();

  const currentPage =
    pageMeta[
      location.pathname
    ] || pageMeta["/"];

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="mobile-menu-button"
          onClick={() =>
            setMobileOpen(true)
          }
          aria-label="Open navigation"
        >
          <Menu size={19} />
        </button>

        <div className="topbar-context" aria-label={`RoadSafe India / ${currentPage.title}`}>
          <img src="/assets/roadsafe-india-mark.png" alt="" className="topbar-brand-mark" />
          <span className="topbar-context-separator">/</span>
          <span>{currentPage.title}</span>
        </div>
      </div>

      <div className="topbar-actions">
        <div className="analysis-context-controls" aria-label="Global analysis context">
          <span>CONTEXT</span>
          <select aria-label="Analysis city" value={analysisContext.city} onChange={(event) => setAnalysisContext((current) => ({ ...current, city: event.target.value }))}>
            <option>All Cities</option>
            {ANALYSIS_CITIES.map((city) => <option key={city}>{city}</option>)}
          </select>
          <select aria-label="Analysis severity" value={analysisContext.severity} onChange={(event) => setAnalysisContext((current) => ({ ...current, severity: event.target.value }))}>
            <option>All Severities</option><option value="fatal">Fatal</option><option value="major">Major</option><option value="minor">Minor</option>
          </select>
          <select aria-label="Analysis period start" value={analysisContext.startYear} onChange={(event) => setAnalysisContext((current) => ({ ...current, startYear: Math.min(Number(event.target.value), current.endYear) }))}>
            {[2022, 2023, 2024, 2025].map((year) => <option key={year}>{year}</option>)}
          </select>
          <span className="context-range-separator">to</span>
          <select aria-label="Analysis period end" value={analysisContext.endYear} onChange={(event) => setAnalysisContext((current) => ({ ...current, endYear: Math.max(Number(event.target.value), current.startYear) }))}>
            {[2022, 2023, 2024, 2025].map((year) => <option key={year}>{year}</option>)}
          </select>
        </div>

        <button type="button" className="command-search" onClick={openCommandPalette}>
          <Search size={14} />
          <span>
            Search intelligence
          </span>
          <kbd>
            Ctrl K
          </kbd>
        </button>

        <div className="api-status">
          <span className="status-dot" />
          API ONLINE
        </div>
      </div>
    </header>
  );
}

/* =========================================================
   SIDEBAR
   ========================================================= */

function Sidebar({
  mobileOpen,
  setMobileOpen,
}) {
  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          className="mobile-backdrop"
          onClick={() =>
            setMobileOpen(false)
          }
          aria-label="Close navigation"
        />
      )}

      <aside
        className={`sidebar ${
          mobileOpen
            ? "sidebar-open"
            : ""
        }`}
      >
        <div className="sidebar-header">
          <NavLink to="/" className="brand" aria-label="RoadSafe India home">
            <img
              src="/assets/roadsafe-india-logo.png"
              alt="RoadSafe India"
              className="sidebar-brand-logo"
            />
          </NavLink>

          <button
            type="button"
            className="sidebar-close"
            onClick={() =>
              setMobileOpen(false)
            }
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <div className="nav-label">
          INTELLIGENCE
        </div>

        <nav className="main-nav">
          {navigation.map(
            ({
              label,
              path,
              icon: Icon,
            }) => (
              <NavLink
                key={path}
                to={path}
                end={path === "/"}
                className={({ isActive }) =>
                  `nav-item ${
                    isActive
                      ? "nav-item-active"
                      : ""
                  }`
                }
                onClick={() =>
                  setMobileOpen(false)
                }
              >
                <Icon size={17} />

                <span>{label}</span>

                {label === "Live Map" && (
                  <span className="nav-live-dot" />
                )}

                {label === "Hotspots" && (
                  <ChevronRight
                    size={13}
                    className="nav-chevron"
                  />
                )}
              </NavLink>
            ),
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot" />

            <div>
              <span className="system-label">
                SYSTEM STATUS
              </span>

              <span className="system-value">
                Operational
              </span>
            </div>
          </div>

          <div className="sidebar-version">
            SPATIAL INTELLIGENCE
            <span>·</span>
            v1.0
          </div>
        </div>
      </aside>
    </>
  );
}

/* =========================================================
   APP
   ========================================================= */

function App() {
  const [mobileOpen, setMobileOpen] =
    useState(false);

  const [analysisContext, setAnalysisContext] = useState(() => {
    try {
      return { ...ANALYSIS_DEFAULTS, ...JSON.parse(localStorage.getItem("roadsafe-analysis-context") || "{}") };
    } catch {
      return ANALYSIS_DEFAULTS;
    }
  });
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [brandSplashVisible, setBrandSplashVisible] = useState(true);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const splashTimer = window.setTimeout(
      () => setBrandSplashVisible(false),
      reducedMotion ? 260 : 3000,
    );
    return () => window.clearTimeout(splashTimer);
  }, []);

  useEffect(() => {
    localStorage.setItem("roadsafe-analysis-context", JSON.stringify(analysisContext));
  }, [analysisContext]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen((open) => !open);
      }
      if (event.key === "Escape") setCommandPaletteOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <AnalysisContext.Provider value={{ analysisContext, setAnalysisContext, openCommandPalette: () => setCommandPaletteOpen(true) }}>
    {brandSplashVisible && (
      <div className="brand-splash" role="status" aria-label="Loading RoadSafe India">
        <img src="/assets/roadsafe-india-logo.png" alt="RoadSafe India" className="brand-splash-logo" />
      </div>
    )}
    <div className="app-shell">
      <Sidebar
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      <div className="main-shell">
        <Topbar
          setMobileOpen={
            setMobileOpen
          }
        />

        {commandPaletteOpen && <CommandPalette onClose={() => setCommandPaletteOpen(false)} />}

        <main className="main-content">
          <PageHeader />

          <Routes>
            <Route
              path="/"
              element={<Overview />}
            />

            <Route
              path="/map"
              element={<LiveMap />}
            />

            <Route
              path="/hotspots"
              element={<Hotspots />}
            />

            <Route
              path="/cities"
              element={<Cities />}
            />

            <Route
              path="/factors"
              element={<RiskFactors />}
            />

            <Route
              path="/history"
              element={
                <HistoricalHistory />
              }
            />

            <Route
              path="/lab"
              element={
                <RoadSafetyLab />
              }
            />

            <Route
              path="/reports"
              element={<Reports />}
            />

            <Route
              path="/methodology"
              element={
                <Methodology />
              }
            />
          </Routes>
        </main>
      </div>
    </div>
    </AnalysisContext.Provider>
  );
}

export default App;

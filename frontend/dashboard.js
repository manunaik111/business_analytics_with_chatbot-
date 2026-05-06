(function () {
    "use strict";
  
    const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    const STORAGE = { rows: "zca_rows", meta: "zca_meta" };
  
    /* ─── Demo fallback data ─────────────────────────────────────────────── */
    const DEMO_ROWS = [
      { region:"West",   cat:"Technology",     sub:"CRM",        product:"Enterprise CRM",    sales:33800, profit:14400, qty:9,  disc:8,  year:2026, month:1 },
      { region:"East",   cat:"Technology",     sub:"Analytics",  product:"Revenue Pulse",     sales:30400, profit:13500, qty:17, disc:6,  year:2026, month:3 },
      { region:"South",  cat:"Services",       sub:"Onboarding", product:"Launch Sprint",     sales:12400, profit:4700,  qty:13, disc:0,  year:2026, month:4 },
      { region:"North",  cat:"Technology",     sub:"Automation", product:"Agent Assist",      sales:19400, profit:8700,  qty:11, disc:3,  year:2026, month:3 },
      { region:"Central",cat:"Furniture",      sub:"Tables",     product:"Retail Demo Table", sales:11800, profit:2100,  qty:8,  disc:14, year:2026, month:2 },
      { region:"West",   cat:"Hardware",       sub:"Devices",    product:"Smart POS Terminal",sales:21600, profit:6200,  qty:24, disc:4,  year:2026, month:1 },
      { region:"East",   cat:"Technology",     sub:"Automation", product:"Workflow Studio",   sales:28700, profit:11800, qty:15, disc:7,  year:2026, month:2 },
      { region:"South",  cat:"Office Supplies",sub:"Paper",      product:"Premium Paper Pack",sales:6200,  profit:1800,  qty:40, disc:5,  year:2026, month:2 },
      { region:"Central",cat:"Technology",     sub:"Analytics",  product:"Forecast Pro",      sales:25100, profit:9900,  qty:13, disc:5,  year:2026, month:2 },
      { region:"North",  cat:"Services",       sub:"Support",    product:"Priority Support",  sales:9800,  profit:4100,  qty:20, disc:0,  year:2026, month:2 },
      { region:"West",   cat:"Office Supplies",sub:"Storage",    product:"Archive Cabinet",   sales:8900,  profit:-600,  qty:6,  disc:18, year:2026, month:4 },
      { region:"East",   cat:"Furniture",      sub:"Chairs",     product:"Executive Chair",   sales:14200, profit:3200,  qty:10, disc:9,  year:2026, month:4 }
    ];
  
    const state = {
      rows: [], filtered: [], meta: {}, charts: {}, recommendations: [], tableRows: [],
      chatOpen: false, voiceActive: false,
      liveTimer: null, liveSource: null,
      voiceWarningShown: false,
      loaderCount: 0,
      userRole: "Viewer"
    };
  
    /* ═══════════════════════════════════════════════════════════════════════
       INIT
    ═══════════════════════════════════════════════════════════════════════ */
    document.addEventListener("DOMContentLoaded", init);
  
    async function init() {
      if (!isAuthenticated()) { window.location.replace("login.html"); return; }
      showLoader("Preparing dashboard...");
      hydrateUser();
      bindUI();
      await refreshDashboard(true);
      startLiveUpdates();
      hideLoader();
    }
  
    function isAuthenticated() {
      return (window.App && App.isAuthenticated()) || localStorage.getItem("isLoggedIn") === "true";
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       USER
    ═══════════════════════════════════════════════════════════════════════ */
    function hydrateUser() {
      const user = window.App && App.getUser ? App.getUser() : null;
      const email   = (user && user.email)  || localStorage.getItem("userEmail") || "admin@sales.com";
      const role    = (user && user.role)   || localStorage.getItem("userRole")  || "Admin";
      const name    = (user && user.name)   || email.split("@")[0].replace(/[._-]+/g," ").replace(/\b\w/g, c => c.toUpperCase());
      const initials= name.split(" ").map(x => x[0]).join("").slice(0,2).toUpperCase();
      state.userRole = role;
  
      safe("navRoleBadge",        el => el.textContent = role);
      safe("sbUserName",          el => el.textContent = name);
      safe("sbUserRole",          el => el.textContent = role);
      safe("sbAvatar",            el => el.textContent = initials);
      safe("sbAvatarCollapsed",   el => el.textContent = initials);
      if (role === "Admin") { safe("usersNavLink", el => el.style.display = "flex"); }
      safe("uploadCard",          el => el.style.display = canUpload(role) ? "" : "none");
    }

    function canUpload(role) {
      return ["Admin", "Sales Manager", "Analyst"].includes(role || state.userRole || "Viewer");
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       UI BINDINGS
    ═══════════════════════════════════════════════════════════════════════ */
    function bindUI() {
      safe("uploadInput",      el => el.addEventListener("change", syncUploadName));
      safe("uploadForm",       el => el.addEventListener("submit", handleUpload));
          safe("refreshNowBtn",    el => el.addEventListener("click",  () => refreshDashboard(false)));
      safe("exportFilteredBtn",el => el.addEventListener("click",  exportFilteredCsv));
      safe("downloadSummaryBtn",el=> el.addEventListener("click",  exportSummaryJson));
      safe("voiceBtn",         el => el.addEventListener("click",  handleVoiceInput));
  
      ["fCat","fRegion","fProfit","fYear"].forEach(id => {
        safe(id, el => el.addEventListener("change", async () => {
          updateFilterDots();
          if (window.App && App.hasConfiguredBackend()) await refreshDashboard(true);
          else renderFromRows();
        }));
      });
  
      safe("sbResetBtn", el => el.addEventListener("click", () => {
        ["fCat","fRegion","fProfit","fYear"].forEach(id => { safe(id, e => e.value = "All"); });
        updateFilterDots();
        if (window.App && App.hasConfiguredBackend()) refreshDashboard(true);
        else renderFromRows();
      }));
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       DASHBOARD REFRESH
    ═══════════════════════════════════════════════════════════════════════ */
    async function refreshDashboard(silent) {
      if (!silent) showLoader("Refreshing analytics...");
      try {
        const payload = await loadBackendPayload();
        applyPayload(payload, "backend");
        if (!silent && App) App.showToast("Dashboard refreshed from backend.", "success");
      } catch (err) {
        const rows = getStoredRows();
        applyPayload(buildLocalPayload(rows), "demo");
        if (!silent && App) App.showToast("Backend unavailable. Using local data.", "warn");
      } finally {
        if (!silent) hideLoader();
      }
    }
  
    async function loadBackendPayload() {
      if (!(window.App && App.hasConfiguredBackend())) throw new Error("No backend");
      const params = getFilterParams();
      const data = await App.request("/api/dashboard/metrics", { params });
      return normalizeBackendPayload(data);
    }
  
    function normalizeBackendPayload(data) {
      const payload = data || {};
      const rows = (payload.rows || payload.records || payload.table || []).map(normalizeRow);
      const local = buildLocalPayload(rows, {
        updatedAt:   payload.updated_at || payload.updatedAt,
        datasetName: (payload.meta && (payload.meta.filename || payload.meta.uploadedFile || payload.meta.uploaded_file)) || "Backend dataset",
        warnings:    (payload.meta && payload.meta.warnings) || [],
        datasetType: (payload.meta && payload.meta.dataset_type) || "generic"
      });
      return {
        rows: local.rows, filtered: local.filtered,
        meta: Object.assign({}, local.meta, { mode: "backend",
          totalRecords:    (payload.total)    || local.meta.totalRecords,
          filteredRecords: (payload.filtered) || local.meta.filteredRecords,
          warnings:        (payload.meta && payload.meta.warnings) || [],
          datasetType:     (payload.meta && payload.meta.dataset_type) || "generic",
          dashboardMode:   (payload.meta && payload.meta.dashboard_mode) || ((payload.meta && payload.meta.dataset_type) === "sales" ? "sales" : "generic"),
          targetColumn:    payload.meta && payload.meta.target_column,
          dateColumn:      payload.meta && payload.meta.date_column,
          categoryColumn:  payload.meta && payload.meta.category_column,
          regionColumn:    payload.meta && payload.meta.region_column,
          itemColumn:      payload.meta && payload.meta.item_column,
          suggestions:     (payload.meta && payload.meta.suggestions) || []
        }),
        filters:  payload.filters  || local.filters,
        kpis:     Array.isArray(payload.kpis)    ? payload.kpis    : local.kpis,
        charts:   payload.charts   || local.charts,
        insights: Array.isArray(payload.insights) ? payload.insights : local.insights,
        recommendations: Array.isArray(payload.recommendations) ? payload.recommendations : [],
        tableRows: Array.isArray(payload.rows) ? payload.rows : []
      };
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       LOCAL PAYLOAD BUILDER
    ═══════════════════════════════════════════════════════════════════════ */
    function buildLocalPayload(rows, meta) {
      const norm     = rows.map(normalizeRow);
      const filters  = {
        categories: unique(norm.map(r => r.cat)),
        regions:    unique(norm.map(r => r.region)),
        years:      unique(norm.map(r => r.year)).sort((a,b) => a-b)
      };
      const filtered     = norm.filter(matchesFilters);
      const totalSales   = sum(filtered,"sales");
      const totalProfit  = sum(filtered,"profit");
      const totalQty     = sum(filtered,"qty");
      const avgDiscount  = filtered.length ? sum(filtered,"disc") / filtered.length : 0;
      const avgOrder     = filtered.length ? totalSales / filtered.length : 0;
      const profitMargin = totalSales ? (totalProfit / totalSales) * 100 : 0;
      const losingCount  = filtered.filter(r => r.profit < 0).length;
      const catSales     = aggregate(filtered,"cat","sales");
      const regProfit    = aggregate(filtered,"region","profit");
      const monthlySales = aggregate(filtered.map(r => ({...r, monthKey:`${r.year}-${String(r.month).padStart(2,"0")}`})),"monthKey","sales");
      const topProds     = aggregate(filtered,"product","sales").slice(0,5);
  
      return {
        rows: norm, filtered,
        meta: {
          updatedAt:       (meta && meta.updatedAt)   || new Date().toISOString(),
          datasetName:     (meta && meta.datasetName) || getStoredMeta().datasetName || "Local demo dataset",
          warnings:        (meta && meta.warnings) || [],
          datasetType:     (meta && meta.datasetType) || "generic",
          dashboardMode:   (meta && meta.datasetType) === "sales" ? "sales" : "generic",
          targetColumn:    (meta && meta.targetColumn) || "Sales",
          dateColumn:      (meta && meta.dateColumn) || "Order Date",
          categoryColumn:  (meta && meta.categoryColumn) || "Category",
          regionColumn:    (meta && meta.regionColumn) || "Region",
          itemColumn:      (meta && meta.itemColumn) || "Product Name",
          suggestions:     (meta && meta.suggestions) || [],
          mode:            "demo",
          totalRecords:    norm.length,
          filteredRecords: filtered.length
        },
        filters,
        kpis: [
          card("Total Sales",    moneyCompact(totalSales),   totalProfit >= 0 ? "Live revenue" : "Revenue alert"),
          card("Total Profit",   moneyCompact(totalProfit),  totalProfit >= 0 ? "Positive margin" : "Negative margin"),
          card("Orders",         filtered.length.toLocaleString("en-US"), `${totalQty.toLocaleString("en-US")} units`),
          card("Avg Discount",   `${avgDiscount.toFixed(1)}%`, avgDiscount > 12 ? "High discounting" : "Controlled"),
          card("Avg Order Value",moneyCompact(avgOrder),     "Filtered average"),
          card("Profit Margin",  `${profitMargin.toFixed(1)}%`, profitMargin >= 0 ? "Margin healthy" : "Margin negative"),
          card("Regions",        String(unique(filtered.map(r => r.region)).length), "Active regions"),
          card("Categories",     String(unique(filtered.map(r => r.cat)).length),    "Active categories")
        ],
        charts: {
          cat:      { labels: catSales.map(x => x.label),   values: catSales.map(x => x.value) },
          monthly:  monthlySeries(filtered),
          products: { labels: topProds.map(x => x.label.slice(0,20)), values: topProds.map(x => x.value) },
          region:   {
            labels: unique(filtered.map(r => r.region)),
            values: unique(filtered.map(r => r.region)).map(reg => filtered.filter(r => r.region === reg).reduce((s,r) => s+r.sales, 0))
          }
        },
        insights: [
          catSales[0]     ? `${catSales[0].label} leads with ${money(catSales[0].value)} in total sales`            : "No category data for current selection",
          regProfit[0]    ? `${regProfit[0].label} shows strongest profit performance`                              : "No regional data for current selection",
          monthlySales[0] ? `${monthLabel(monthlySales[0].label)} has highest sales volume`                         : "No monthly peak available",
          filtered.length ? `${((losingCount/filtered.length)*100).toFixed(1)}% of transactions recorded at a loss` : "No loss data for current selection"
        ],
        recommendations: [
          avgDiscount > 12 ? "Reduce discount levels to protect margin." : "Monitor pricing and discounting by segment.",
          catSales[0] ? `Review performance by ${catSales[0].label} because it leads the current selection.` : "Apply filters to compare categories or regions.",
          regProfit[0] ? `Use ${regProfit[0].label} as a benchmark for regional performance.` : "Compare results across regions to find strong and weak areas."
        ],
        tableRows: filtered.slice(0, 100).map(r => ({
          Region: r.region,
          Category: r.cat,
          "Sub-Category": r.sub,
          "Product Name": r.product,
          Sales: r.sales,
          Profit: r.profit,
          Quantity: r.qty,
          Discount: r.disc,
          "Order Date": `${r.year}-${String(r.month).padStart(2, "0")}`
        }))
      };
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       APPLY PAYLOAD
    ═══════════════════════════════════════════════════════════════════════ */
    function applyPayload(payload, mode) {
      state.rows     = payload.rows     || [];
      state.filtered = payload.filtered || [];
      state.meta     = payload.meta     || {};
      state.recommendations = payload.recommendations || [];
      state.tableRows = payload.tableRows || [];
      populateFilters(payload.filters   || {});
      renderSidebarStats();
      renderKpis(payload.kpis           || []);
      renderCharts(payload.charts       || {});
      renderInsights(payload.insights   || []);
      renderDashboardLabels();
      renderQuickTags();
      renderTable();
      updateStatus(mode);
      updateFilterDots();
    }
  
    function renderFromRows() {
      applyPayload(buildLocalPayload(state.rows, state.meta), state.meta.mode || "demo");
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       FILTERS
    ═══════════════════════════════════════════════════════════════════════ */
    function populateFilters(filters) {
      fillSelect("fCat",    filters.categories || []);
      fillSelect("fRegion", filters.regions    || []);
      fillSelect("fYear",   (filters.years || []).map(String));
    }
  
    function fillSelect(id, values) {
      const el = document.getElementById(id);
      if (!el) return;
      const cur   = el.value || "All";
      const items = ["All"].concat(unique(values).map(String));
      el.innerHTML = items.map(v => `<option value="${esc(v)}">${esc(v === "All" ? labelForSelect(id) : v)}</option>`).join("");
      el.value = items.includes(cur) ? cur : "All";
    }
  
    function labelForSelect(id) {
      if (id === "fCat")    return "All Categories";
      if (id === "fRegion") return "All Regions";
      if (id === "fYear")   return "All Years";
      return "All";
    }
  
    function matchesFilters(row) {
      const cat    = val("fCat");
      const region = val("fRegion");
      const profit = val("fProfit");
      const year   = val("fYear");
      if (cat    !== "All" && row.cat    !== cat)    return false;
      if (region !== "All" && row.region !== region) return false;
      if (year   !== "All" && String(row.year) !== String(year)) return false;
      if (profit === "Profitable"   && row.profit <= 0) return false;
      if (profit === "Unprofitable" && row.profit >= 0) return false;
      return true;
    }
  
    function getFilterParams() {
      return { category: val("fCat"), region: val("fRegion"), profit: val("fProfit"), year: val("fYear") };
    }
  
    function updateFilterDots() {
      const map = { fCat:"dotCat", fRegion:"dotRegion", fProfit:"dotProfit", fYear:"dotYear" };
      Object.entries(map).forEach(([sid, did]) => {
        const dot = document.getElementById(did);
        if (dot) dot.classList.toggle("active", val(sid) !== "All");
      });
    }

    function isSalesMode() {
      return state.meta.dashboardMode === "sales" || state.meta.datasetType === "sales";
    }

    function primaryMetricLabel() {
      return state.meta.targetColumn || (isSalesMode() ? "Sales" : "Value");
    }

    function dateMetricLabel() {
      return state.meta.dateColumn || "Date";
    }

    function categoryMetricLabel() {
      return state.meta.categoryColumn || "Category";
    }

    function regionMetricLabel() {
      return state.meta.regionColumn || "Region";
    }

    function itemMetricLabel() {
      return state.meta.itemColumn || "Item";
    }

    function renderDashboardLabels() {
      const target = primaryMetricLabel();
      const category = categoryMetricLabel();
      const region = regionMetricLabel();
      const item = itemMetricLabel();
      const date = dateMetricLabel();
      const salesMode = isSalesMode();

      safe("chartSectionTitle", el => el.textContent = salesMode ? "Sales and Profit Analysis" : "Dataset Analysis");
      safe("chartMonthlyTitle", el => el.textContent = `Monthly ${target} Trend`);
      safe("chartCatTitle", el => el.textContent = `${target} by ${category}`);
      safe("chartProductsTitle", el => el.textContent = `Top 5 ${item}s by ${target}`);
      safe("chartRegionTitle", el => el.textContent = `${target} by ${region}`);
      safe("chatHeaderTitle", el => el.textContent = salesMode ? "AI Sales Assistant" : "AI Dataset Assistant");
      safe("chatInput", el => el.placeholder = salesMode ? "Ask about this sales dataset..." : "Ask about this dataset...");
      const firstBot = document.querySelector("#chatMsgs .msg-bot");
      if (firstBot && firstBot.dataset.seeded !== "true") {
        firstBot.innerHTML = salesMode
          ? "Hello. I am your AI Sales Assistant.<br>Ask me anything about the sales data."
          : "Hello. I am your AI Dataset Assistant.<br>Ask me about columns, trends, quality, or summaries.";
        firstBot.dataset.seeded = "true";
      }
    }

    function renderQuickTags() {
      const wrap = document.getElementById("quickTags");
      if (!wrap) return;

      const suggestions = Array.isArray(state.meta.suggestions) && state.meta.suggestions.length
        ? state.meta.suggestions.slice(0, 4)
        : buildFallbackQuickTags();

      wrap.innerHTML = suggestions.map(q => (
        `<button class="quick-tag" onclick='quickAsk(${JSON.stringify(q)})'>${esc(shortQuickTag(q))}</button>`
      )).join("");
    }

    function buildFallbackQuickTags() {
      const target = primaryMetricLabel();
      const category = categoryMetricLabel();
      const region = regionMetricLabel();
      const item = itemMetricLabel();
      const date = dateMetricLabel();

      if (isSalesMode()) {
        return [
          `Which ${region} has the highest ${target}?`,
          `Which ${category} has the highest profit?`,
          `What are the top 5 ${item}s?`,
          `Show me the monthly ${target} trend`
        ];
      }

      return [
        "What columns does this dataset have?",
        `What is the average ${target}?`,
        `Show me the monthly ${target} trend using ${date}`,
        `Which ${category} or ${region} appears most often?`
      ];
    }

    function shortQuickTag(text) {
      const q = String(text || "").trim();
      if (q.length <= 28) return q;
      return q.slice(0, 27).trim() + "...";
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       RENDER — SIDEBAR
    ═══════════════════════════════════════════════════════════════════════ */
    function renderSidebarStats() {
      safe("sbStatRows",  el => el.textContent = number(state.meta.totalRecords || state.rows.length).toLocaleString("en-US"));
      safe("sbStatYears", el => el.textContent = unique(state.rows.map(r => r.year)).length.toLocaleString("en-US"));
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       RENDER — KPIs
    ═══════════════════════════════════════════════════════════════════════ */
    const KPI_COLORS = ["#DC2626","#9CA3AF","#4ADE80","#D97706","#F43F5E","#FB923C","#67E8F9","#A5B4FC"];
  
    function renderKpis(cards) {
      const all = (cards || []).slice(0,8);
      const build = (item, i) => `
        <div class="kpi-card">
          <div class="kpi-bar" style="background:${KPI_COLORS[i]||"#DC2626"}"></div>
          <div class="kpi-body">
            <div class="kpi-top-row">
              <div class="kpi-label">${esc(item.label||`KPI ${i+1}`)}</div>
              <div class="kpi-icon">${["S","P","O","D","A","M","R","C"][i]||"K"}</div>
            </div>
            <div class="kpi-value">${esc(item.value||"0")}</div>
            <div class="kpi-sub">${esc(item.sub||"Live metric")}</div>
          </div>
        </div>`;
      safe("kpiRow1", el => el.innerHTML = all.slice(0,4).map(build).join(""));
      safe("kpiRow2", el => el.innerHTML = all.slice(4,8).map(build).join(""));
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       RENDER — CHARTS
    ═══════════════════════════════════════════════════════════════════════ */
    function renderCharts(charts) {
      drawDoughnut("chartCat", charts.cat && charts.cat.labels && charts.cat.labels.length ? charts.cat : { labels:["No data"], values:[1] });
      drawLine("chartMonthly", charts.monthly && charts.monthly.labels && charts.monthly.labels.length ? charts.monthly : { labels:[`No ${dateMetricLabel()}`], values:[0] });
      drawHorizontalBar("chartProducts", charts.products && charts.products.labels && charts.products.labels.length ? charts.products : { labels:["No grouped items"], values:[0] });
      drawBar("chartRegion", charts.region && charts.region.labels && charts.region.labels.length ? charts.region : { labels:[`No ${regionMetricLabel()}`], values:[0] });
      drawScatter("chartScatter", buildScatterSeries(state.filtered));
      drawHeatmap("chartHeatmap", buildHeatmapSeries(state.filtered));
    }
  
    function drawDoughnut(id, chart) {
      drawChart(id, "doughnut", {
        labels: chart.labels,
        datasets: [{ data: chart.values, backgroundColor:["#8B0020","#DC2626","#9CA3AF","#D97706","#4ADE80"], borderWidth:0 }]
      }, { plugins:{ legend:{ labels:{ color:"#888", font:{ size:10 } } } } });
    }
  
    function drawLine(id, chart) {
      drawChart(id, "line", {
        labels: chart.labels,
        datasets: [{ data:chart.values, borderColor:"#8B0020", borderWidth:2.5, tension:0.4,
                     pointBackgroundColor:"#DC2626", pointRadius:4,
                     fill:true, backgroundColor:"rgba(109,0,26,0.10)" }]
      }, lineScales());
    }
  
    function drawHorizontalBar(id, chart) {
      drawChart(id, "bar", {
        labels: chart.labels,
        datasets: [{ data:chart.values, backgroundColor:["rgba(109,0,26,0.85)","rgba(85,0,20,0.75)","rgba(60,0,14,0.65)","rgba(40,40,40,0.75)","rgba(28,28,28,0.65)"], borderRadius:4 }]
      }, Object.assign({ indexAxis:"y" }, lineScales()));
    }
  
    function drawBar(id, chart) {
      drawChart(id, "bar", {
        labels: chart.labels,
        datasets: [{ data:chart.values, backgroundColor:["rgba(109,0,26,0.85)","rgba(65,65,65,0.85)","rgba(42,42,42,0.78)","rgba(26,26,26,0.75)"], borderRadius:5 }]
      }, lineScales());
    }

    function drawScatter(id, series) {
      const labels = series.labels || [];
      const points = (series.points || []).map((p, i) => ({ x: p.x, y: p.y, _label: labels[i] || `Point ${i + 1}` }));
      drawChart(id, "scatter", {
        datasets: [{
          label: "Transactions",
          data: points,
          pointRadius: 4,
          pointHoverRadius: 5,
          showLine: false,
          backgroundColor: "rgba(220,38,38,0.75)",
          borderColor: "rgba(220,38,38,0.95)",
          borderWidth: 1
        }]
      }, {
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => {
                const p = ctx.raw || {};
                return `${p._label || "Record"}: ${moneyCompact(p.x || 0)} sales, ${moneyCompact(p.y || 0)} profit`;
              }
            }
          }
        },
        scales: {
          x: { grid:{ color:"rgba(255,255,255,0.06)" }, ticks:{ color:"#666", callback: v => moneyCompact(v) } },
          y: { grid:{ color:"rgba(255,255,255,0.06)" }, ticks:{ color:"#666", callback: v => moneyCompact(v) } }
        }
      });
    }

    function drawHeatmap(id, series) {
      const points = series.points || [];
      const xLabels = series.xLabels || [];
      const yLabels = series.yLabels || [];
      const maxValue = points.reduce((m, p) => Math.max(m, p.v || 0), 0) || 1;
      const bubbleData = points.map(p => {
        const intensity = (p.v || 0) / maxValue;
        return {
          x: p.x,
          y: p.y,
          r: 4 + Math.round(intensity * 9),
          v: p.v,
          monthLabel: xLabels[p.x] || "",
          regionLabel: yLabels[p.y] || ""
        };
      });
      drawChart(id, "bubble", {
        datasets: [{
          label: "Region-Month intensity",
          data: bubbleData,
          backgroundColor: bubbleData.map(p => `rgba(220,38,38,${0.2 + Math.min(0.7, (p.v || 0) / maxValue)})`),
          borderColor: "rgba(220,38,38,0.9)",
          borderWidth: 1
        }]
      }, {
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => {
                const p = ctx.raw || {};
                return `${p.regionLabel || "Region"} / ${p.monthLabel || "Month"}: ${moneyCompact(p.v || 0)}`;
              }
            }
          }
        },
        scales: {
          x: {
            type: "linear",
            min: -0.5,
            max: Math.max(0.5, xLabels.length - 0.5),
            ticks: {
              color: "#666",
              stepSize: 1,
              callback: v => Number.isInteger(v) && xLabels[v] ? xLabels[v] : ""
            },
            grid: { color:"rgba(255,255,255,0.06)" }
          },
          y: {
            type: "linear",
            min: -0.5,
            max: Math.max(0.5, yLabels.length - 0.5),
            ticks: {
              color: "#666",
              stepSize: 1,
              callback: v => Number.isInteger(v) && yLabels[v] ? yLabels[v] : ""
            },
            grid: { color:"rgba(255,255,255,0.06)" }
          }
        }
      });
    }
  
    function drawChart(id, type, data, options) {
      if (state.charts[id]) state.charts[id].destroy();
      const base = { responsive:true, maintainAspectRatio:false,
                     plugins:{ legend:{ display:type==="doughnut", labels:{ color:"#999" } } } };
      const canvas = document.getElementById(id);
      if (!canvas) return;
      state.charts[id] = new Chart(canvas, { type, data, options:Object.assign(base, options||{}) });
    }
  
    function lineScales() {
      return {
        plugins:{ legend:{ display:false } },
        scales:{
          x:{ grid:{ color:"rgba(255,255,255,0.06)" }, ticks:{ color:"#666", font:{ size:10 } } },
          y:{ grid:{ color:"rgba(255,255,255,0.06)" }, ticks:{ color:"#666", font:{ size:10 }, callback: v => isSalesMode() ? moneyCompact(v) : numberCompact(v) } }
        }
      };
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       RENDER — INSIGHTS
    ═══════════════════════════════════════════════════════════════════════ */
    function renderInsights(insights) {
      // Update insight chips
      const chipIds = ["insightChip0","insightChip1","insightChip2","insightChip3"];
      chipIds.forEach((id, i) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = insights[i] || "No insight available";
        el.style.color = "";  // restore chip color
      });
      // Update recommendations panel
      renderRecommendations(state.recommendations);
      // Async Groq AI chip
      fetchAiInsight();
    }
  
    function renderRecommendations(recommendations) {
      const list = document.getElementById("recList");
      if (!list) return;
      const recs = (Array.isArray(recommendations) ? recommendations : []).filter(Boolean);
      if (!recs.length) {
        list.innerHTML = '<div class="rec-item"><span style="color:var(--text-hint)">Upload data to generate recommendations.</span></div>';
        return;
      }

      const colors = ["#F87171", "#FB923C", "#4ADE80", "#818CF8", "#38BDF8"];
      list.innerHTML = recs.slice(0,5).map((text, idx) =>
        `<div class="rec-item"><span class="rec-dot" style="background:${colors[idx % colors.length]}"></span><span>${esc(text)}</span></div>`
      ).join("");
    }
  
    async function fetchAiInsight() {
      const chip = document.getElementById("insightChipAI");
      if (!chip) return;
      if (!window.App || !App.hasConfiguredBackend()) {
        chip.textContent = "Connect backend to enable Groq AI insights.";
        chip.classList.add("chip-ai-loading");
        return;
      }
      chip.textContent = "Generating AI insight...";
      chip.classList.add("chip-ai-loading");
      try {
        const summary = `${state.filtered.length} rows filtered. ` +
          `Dataset mode: ${isSalesMode() ? "sales" : "generic"}. ` +
          `Target column: ${primaryMetricLabel()}. ` +
          `Date column: ${dateMetricLabel()}. ` +
          `Top grouping: ${state.meta.categoryColumn || state.meta.regionColumn || "N/A"}.`;
        const resp = await App.request("/api/chat/message", {
          method: "POST",
          body: { message: `One sharp dataset insight under 18 words: ${summary}`, filters: getFilterParams(), rows: [] }
        });
        const text = (resp.reply || resp.answer || "").replace(/<[^>]*>/g,"").trim();
        chip.textContent = text || "No AI insight available.";
        chip.classList.remove("chip-ai-loading");
      } catch(e) {
        chip.textContent = "AI insight unavailable.";
        chip.classList.add("chip-ai-loading");
      }
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       RENDER — TABLE
    ═══════════════════════════════════════════════════════════════════════ */
    function renderTable() {
      const rows = (state.tableRows && state.tableRows.length ? state.tableRows : state.filtered.slice(0,15));
      const tbody = document.getElementById("tBody");
      if (!tbody) return;
      const columns = rows.length ? Object.keys(rows[0]).slice(0, 9) : ["No data"];
      safe("tableHead", el => {
        el.innerHTML = `<tr>${columns.map(col => `<th>${esc(col)}</th>`).join("")}</tr>`;
      });
      tbody.innerHTML = rows.map(r => `
        <tr>
          ${columns.map(col => `<td>${formatCell(col, r[col])}</td>`).join("")}
        </tr>`).join("");
      safe("tableTitleText", el => {
        el.textContent = `Showing ${rows.length} of ${number(state.meta.filteredRecords || state.filtered.length).toLocaleString("en-US")} filtered records`;
      });
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       STATUS
    ═══════════════════════════════════════════════════════════════════════ */
    function updateStatus(mode) {
      const live = mode === "backend";
      safe("backendModeBadge", el => {
        el.textContent = live ? "Backend Mode" : "Demo Mode";
        el.className   = `badge ${live ? "badge-green" : "badge-amber"}`;
      });
      safe("tableStatusBadge", el => {
        el.textContent = live ? "Live Backend" : "Local Data";
        el.className   = `badge ${live ? "badge-green" : "badge-burg"}`;
      });
      safe("activeDatasetName",  el => el.textContent = state.meta.datasetName || "Dataset");
      safe("activeDatasetRows",  el => el.textContent = `${number(state.meta.totalRecords || state.rows.length).toLocaleString("en-US")} rows`);
      safe("topbarDatasetName",  el => el.textContent = state.meta.datasetName || "No dataset loaded");
      safe("lastUpdatedText",    el => el.textContent = formatDate(state.meta.updatedAt));
      renderUploadWarnings(state.meta.warnings || []);
      // Topbar live indicator
      const dot  = document.getElementById("liveIndicatorDot");
      const txt  = document.getElementById("liveIndicatorText");
      if (dot) { dot.className = `live-dot${live ? "" : " demo"}`; }
      if (txt) { txt.textContent = live ? "Live Backend" : "Demo Mode"; }
    }

    function renderUploadWarnings(warnings) {
      safe("uploadWarnings", el => {
        const list = massageWarnings(Array.isArray(warnings) ? warnings.filter(Boolean) : []);
        if (!list.length) {
          el.style.display = "none";
          el.innerHTML = "";
          return;
        }
        el.style.display = "block";
        el.innerHTML = list.map(w => `<div>${esc(w)}</div>`).join("");
      });
    }

    function massageWarnings(warnings) {
      return warnings.map(w => {
        if (/No 'Category' column detected/i.test(w) && state.meta.categoryColumn && state.meta.categoryColumn !== "Category") {
          return `Using ${state.meta.categoryColumn} as the grouping column for category-style breakdowns.`;
        }
        if (/No 'Region' column detected/i.test(w) && state.meta.regionColumn && state.meta.regionColumn !== "Region") {
          return `Using ${state.meta.regionColumn} for region-style charts and filters.`;
        }
        if (/Date column not mapped to 'Order Date'/i.test(w) && state.meta.dateColumn && state.meta.dateColumn !== "Order Date") {
          return `Using ${state.meta.dateColumn} for time-based charts and filters.`;
        }
        return w;
      });
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       FILE UPLOAD
    ═══════════════════════════════════════════════════════════════════════ */
    async function handleUpload(event) {
      event.preventDefault();
      const input = document.getElementById("uploadInput");
      const file  = input && input.files && input.files[0];
      if (!file) { if (App) App.showToast("Select a file first.", "error"); return; }
      showLoader("Uploading dataset...");
  
      if (window.App && App.hasConfiguredBackend()) {
        try {
          const fd = new FormData();
          fd.append("file", file);
          const result = await App.request("/api/dashboard/upload", { method:"POST", body:fd });
          renderUploadWarnings(result.warnings || []);
          if (App) App.showToast(`${file.name} uploaded to backend.`, "success");
          if (result.warnings && result.warnings.length && App) App.showToast("Uploaded with dataset-specific limitations.", "warn");
          await refreshDashboard(true);
          hideLoader();
          return;
        } catch (err) {
          if (err && (err.status === 401 || err.status === 403)) {
            hideLoader();
            if (App) App.showToast(err.message || "Your role cannot upload datasets.", "error");
            return;
          }
          if (App) App.showToast("Backend upload failed. Parsing locally.", "warn");
        }
      }
  
      /* Local parse fallback */
      try {
        const rows = await parseFile(file);
        localStorage.setItem(STORAGE.rows, JSON.stringify(rows));
        localStorage.setItem(STORAGE.meta, JSON.stringify({ datasetName:file.name, updatedAt:new Date().toISOString() }));
        state.meta = getStoredMeta();
        state.rows = rows;
        renderFromRows();
        if (App) App.showToast(`Loaded ${rows.length} rows from ${file.name}.`, "success");
      } catch (err) {
        if (App) App.showToast("Could not parse file. Try CSV or Excel.", "error");
      } finally {
        hideLoader();
      }
    }
  
    function syncUploadName() {
      const file = document.getElementById("uploadInput").files[0];
      safe("uploadFileName", el => el.textContent = file ? file.name : "No file selected");
    }
  
    async function parseFile(file) {
      const buffer   = await file.arrayBuffer();
      const workbook = XLSX.read(buffer, { type:"array" });
      const sheet    = workbook.Sheets[workbook.SheetNames[0]];
      const json     = XLSX.utils.sheet_to_json(sheet, { defval:"" });
      return json.map(normalizeRow).filter(r => r.sales || r.profit || r.qty);
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       ROW NORMALIZATION
    ═══════════════════════════════════════════════════════════════════════ */
    function normalizeRow(row) {
      const src = row || {};
      const lk  = {};
      Object.keys(src).forEach(k => { lk[k.toLowerCase().replace(/[^a-z0-9]/g,"")] = src[k]; });
      const dateVal = pick(lk,["date","orderdate","transactiondate","createdat"]);
      const date    = dateVal ? new Date(dateVal) : null;
      const year    = number(pick(lk,["year"])) || (date && !isNaN(date) ? date.getFullYear() : new Date().getFullYear());
      const month   = number(pick(lk,["month"])) || (date && !isNaN(date) ? date.getMonth()+1 : 1);
      let disc      = number(pick(lk,["discount","disc","discountpercent","discountpct"]));
      if (disc > 0 && disc < 1) disc *= 100;
      return {
        region:  text(pick(lk,["region","market","territory"]),  "Unknown"),
        cat:     text(pick(lk,["category","cat"]),               "General"),
        sub:     text(pick(lk,["subcategory","sub","segment"]),  "General"),
        product: text(pick(lk,["product","productname","item","sku"]), "Unnamed item"),
        sales:   number(pick(lk,["sales","revenue","amount","total","totalsales"])),
        profit:  number(pick(lk,["profit","margin","netprofit"])),
        qty:     Math.max(1, Math.round(number(pick(lk,["qty","quantity","units","orders"]))||1)),
        disc:    Math.round((disc||0)*10)/10,
        year:    Math.round(year),
        month:   Math.min(12, Math.max(1, Math.round(month)))
      };
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       LIVE UPDATES (authenticated polling)
    ═══════════════════════════════════════════════════════════════════════ */
    function startLiveUpdates() {
      if (state.liveTimer) clearInterval(state.liveTimer);
      state.liveTimer = setInterval(() => refreshDashboard(true), 30000);
      if (state.liveSource) {
        state.liveSource.close();
        state.liveSource = null;
      }
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       CHAT
    ═══════════════════════════════════════════════════════════════════════ */
    function toggleChat() {
      state.chatOpen = !state.chatOpen;
      const panel = document.getElementById("chatPanel");
      const fab   = document.getElementById("chatFab");
      if (panel) panel.classList.toggle("open", state.chatOpen);
      if (!fab) return;
      fab.innerHTML = state.chatOpen
        ? `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Close`
        : `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> AI Assistant`;
    }
  
    function quickAsk(q) {
      const inp = document.getElementById("chatInput");
      if (inp) inp.value = q;
      sendMsg();
    }
  
    async function sendMsg() {
      const inp  = document.getElementById("chatInput");
      const text = (inp && inp.value.trim()) || "";
      if (!text) return;
      if (inp) inp.value = "";
      addMsg(text, "user");
      const typing = addMsg('<span class="dot-typing"><span></span><span></span><span></span></span>', "bot", true);
  
      if (window.App && App.hasConfiguredBackend()) {
        try {
          const resp = await App.request("/api/chat/message", {
            method: "POST",
            body:   { message:text, filters:getFilterParams(), rows:state.filtered.slice(0,50) }
          });
          const reply = resp.reply || resp.answer || "No reply from backend.";
          if (Array.isArray(resp.suggestions) && resp.suggestions.length) {
            state.meta.suggestions = resp.suggestions;
            renderQuickTags();
          }
          removeMsg(typing);
          addMsg(reply, "bot");
          if (window.App && App.hasConfiguredBackend()) speakReply(reply);
          return;
        } catch (e) {
          removeMsg(typing);
          if (App) App.showToast((e && e.message) || "Chat service unavailable. Using local assistant.", "warn");
        }
      }
      const local = localReply(text);
      removeMsg(typing);
      addMsg(local, "bot");
      speakReply(local);
    }
  
    function addMsg(text, role, isHtml) {
      const el = document.createElement("div");
      el.className = `msg msg-${role}`;
      el.innerHTML = (role === "bot" && isHtml) ? text : (role === "bot" ? text : esc(text));
      const w = document.getElementById("chatMsgs");
      if (!w) return null;
      w.appendChild(el);
      w.scrollTop = w.scrollHeight;
      return el;
    }

    function removeMsg(node) {
      if (node && node.parentNode) node.parentNode.removeChild(node);
    }
  
    function localReply(text) {
      const lower = text.toLowerCase();
      if (!state.filtered.length) return "No data available for the current filters.";
      if (lower.includes("column") || lower.includes("schema")) {
        const cols = state.tableRows.length ? Object.keys(state.tableRows[0]) : [];
        return cols.length ? `This dataset includes: <b>${cols.map(esc).join(", ")}</b>.` : "No table columns available.";
      }
      if (lower.includes("region")) {
        const target = detectTargetMetric();
        const top = aggregate(state.filtered,"region",target)[0];
        return top ? `<b>${esc(top.label)}</b> leads based on ${esc(metricLabelFor(target))}.` : "No region-style grouping is available.";
      }
      if (lower.includes("category") || lower.includes("cat")) {
        const target = detectTargetMetric();
        const top = aggregate(state.filtered,"cat",target)[0];
        return top ? `<b>${esc(top.label)}</b> is leading based on ${esc(metricLabelFor(target))}.` : "No category-style grouping is available.";
      }
      if (lower.includes("top") || lower.includes("product")) {
        const target = detectTargetMetric();
        return aggregate(state.filtered,"product",target).slice(0,5)
          .map((x,i) => `${i+1}. ${esc(x.label)} — ${formatMetricValue(target, x.value)}`).join("<br>");
      }
      if (lower.includes("month") || lower.includes("trend")) {
        const target = detectTargetMetric();
        const top = aggregate(state.filtered.map(r => ({...r, ml:`${MONTHS[r.month-1]} ${r.year}`})),"ml",target)[0];
        return top ? `Peak month: <b>${esc(top.label)}</b> with <b>${formatMetricValue(target, top.value)}</b>.` : "No monthly data.";
      }
      if (lower.includes("profit")) {
        const totalP = sum(state.filtered,"profit");
        const margin = sum(state.filtered,"sales") ? (totalP / sum(state.filtered,"sales") * 100).toFixed(1) : 0;
        return `Total profit: <b>${money(totalP)}</b>. Profit margin: <b>${margin}%</b>.`;
      }
      if (lower.includes("average") || lower.includes("mean")) {
        const target = detectTargetMetric();
        const total = sum(state.filtered, target);
        const avg = state.filtered.length ? total / state.filtered.length : 0;
        return `Average ${esc(metricLabelFor(target))}: <b>${formatMetricValue(target, avg)}</b>.`;
      }
      if (lower.includes("upload") || lower.includes("dataset")) {
        return `Current dataset: <b>${esc(state.meta.datasetName||"Dataset")}</b> · <b>${number(state.meta.totalRecords || state.rows.length)}</b> rows.`;
      }
      return `I analyzed "<b>${esc(text)}</b>". Ask about columns, trends, top groups, averages, or the active dataset.`;
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       VOICE INPUT
    ═══════════════════════════════════════════════════════════════════════ */
    async function handleVoiceInput() {
      const btn = document.getElementById("voiceBtn");
  
      /* Try Web Speech API first (browser native, no server needed) */
      if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new SR();
        rec.lang = "en-US";
        rec.interimResults = false;
        if (btn) { btn.classList.add("recording"); btn.setAttribute("aria-label","Listening…"); }
        rec.onresult = (e) => {
          const transcript = e.results[0][0].transcript;
          const inp = document.getElementById("chatInput");
          if (inp) inp.value = transcript;
          sendMsg();
        };
        rec.onerror = () => {
          if (btn) { btn.classList.remove("recording"); }
          if (App) App.showToast("Could not capture voice. Check microphone permissions.", "error");
        };
        rec.onend = () => { if (btn) btn.classList.remove("recording"); };
        rec.start();
        return;
      }
  
      /* Fallback: record via MediaRecorder and send to backend */
      if (!window.App || !App.hasConfiguredBackend()) {
        if (App) App.showToast("Voice input requires backend or browser speech support.", "warn");
        return;
      }
  
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio:true });
        if (btn) { btn.classList.add("recording"); btn.setAttribute("aria-label","Recording…"); }
        const recorder = new MediaRecorder(stream);
        const chunks   = [];
        recorder.ondataavailable = e => chunks.push(e.data);
        recorder.onstop = async () => {
          if (btn) btn.classList.remove("recording");
          stream.getTracks().forEach(t => t.stop());
          const blob = new Blob(chunks, { type:"audio/webm" });
          const fd   = new FormData();
          fd.append("audio", blob, "voice.webm");
          try {
            const resp = await App.request("/api/voice/transcribe", { method:"POST", body:fd });
            const text = resp.text || "";
            if (text) {
              const inp = document.getElementById("chatInput");
              if (inp) inp.value = text;
              sendMsg();
            } else {
              if (App) App.showToast("Could not transcribe audio.", "warn");
            }
          } catch (e) {
            const voiceMsg = e && e.status === 503
              ? "Voice is optional and currently unavailable on this deployment."
              : (e && e.message) || "Voice transcription failed.";
            if (App) App.showToast(voiceMsg, e && e.status === 503 ? "warn" : "error");
          }
        };
        recorder.start();
        setTimeout(() => recorder.stop(), 5000); /* auto-stop after 5s */
      } catch (e) {
        if (btn) btn.classList.remove("recording");
        if (App) App.showToast("Microphone access denied.", "error");
      }
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       VOICE OUTPUT
    ═══════════════════════════════════════════════════════════════════════ */

    // Preferred female voice names — ordered by quality (best first)
    const PREFERRED_VOICES = [
      "Google UK English Female",   // Chrome — best quality
      "Google US English",          // Chrome fallback (tends to be female)
      "Microsoft Zira - English (United States)",   // Edge / Windows
      "Microsoft Jenny Online (Natural) - English (United States)", // Edge Neural
      "Microsoft Aria Online (Natural) - English (United States)",  // Edge Neural
      "Samantha",                   // macOS / iOS — natural female
      "Karen",                      // macOS Australian female
      "Moira",                      // macOS Irish female
      "Tessa",                      // macOS South African female
      "Victoria",                   // macOS female
    ];

    function _pickBestVoice() {
      const voices = window.speechSynthesis.getVoices();
      if (!voices.length) return null;

      // 1 — Try exact preferred name match
      for (const name of PREFERRED_VOICES) {
        const v = voices.find(v => v.name === name);
        if (v) return v;
      }

      // 2 — Any Google English female
      const googleFemale = voices.find(v =>
        v.name.toLowerCase().includes("google") &&
        v.lang.startsWith("en") &&
        v.name.toLowerCase().includes("female")
      );
      if (googleFemale) return googleFemale;

      // 3 — Any voice with "female" in the name
      const namedFemale = voices.find(v =>
        v.name.toLowerCase().includes("female") && v.lang.startsWith("en")
      );
      if (namedFemale) return namedFemale;

      // 4 — Any English voice that isn't explicitly male
      const englishVoice = voices.find(v =>
        v.lang.startsWith("en") && !v.name.toLowerCase().includes("male")
      );
      return englishVoice || voices[0];
    }

    async function speakReply(text) {
      const plainText = text.replace(/<[^>]*>/g,"").trim();
      if (!plainText) return;
  
      /* Use browser TTS if available */
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();

        const _speak = () => {
          const utt   = new SpeechSynthesisUtterance(plainText);
          const voice = _pickBestVoice();
          if (voice) utt.voice = voice;
          utt.lang  = "en-US";
          utt.rate  = 0.95;   // slightly slower = more natural, less robotic
          utt.pitch = 1.05;   // slight lift = warmer, more human feel
          utt.volume = 1.0;
          window.speechSynthesis.speak(utt);
        };

        // Voices may not be loaded yet on first call — wait for them
        if (window.speechSynthesis.getVoices().length > 0) {
          _speak();
        } else {
          window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.onvoiceschanged = null;
            _speak();
          };
        }
        return;
      }
  
      /* Fallback: backend TTS */
      if (!window.App || !App.hasConfiguredBackend()) return;
      try {
        const resp = await fetch(App.buildApiUrl("/api/voice/speak"), {
          method:"POST",
          headers:{ "Content-Type":"application/json", "Authorization":`Bearer ${localStorage.getItem("sales_auth_token")||""}` },
          body: JSON.stringify({ text: plainText })
        });
        if (!resp.ok) {
          if (resp.status === 503 && App && !state.voiceWarningShown) {
            App.showToast("Voice output is optional and currently unavailable.", "warn");
            state.voiceWarningShown = true;
          }
          return;
        }
        const blob = await resp.blob();
        const url  = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        audio.play();
      } catch (e) {}
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       EXPORTS
    ═══════════════════════════════════════════════════════════════════════ */
  
    /* ═══════════════════════════════════════════════════════════════════════
       REPORT DOWNLOADS — PDF + EXCEL via backend
    ═══════════════════════════════════════════════════════════════════════ */
    async function downloadPDF() {
      if (!window.App || !App.hasConfiguredBackend()) {
        if (App) App.showToast("Backend required for PDF reports.", "warn"); return;
      }
      if (App) App.showToast("Generating PDF report...", "info");
      try {
        const params = getFilterParams();
        const query  = Object.entries(params)
          .filter(([,v]) => v && v !== "All")
          .map(([k,v]) => k + "=" + encodeURIComponent(v)).join("&");
        const url = App.buildApiUrl("/api/reports/pdf") + (query ? "?" + query : "");
        const token = localStorage.getItem("sales_auth_token") || "";
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Authorization": "Bearer " + token }
        });
        if (!resp.ok) throw new Error("Report generation failed.");
        const blob = await resp.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${slugify(state.meta.datasetName || (isSalesMode() ? "sales-report" : "dataset-report"))}.pdf`;
        a.click();
        URL.revokeObjectURL(a.href);
        if (App) App.showToast("PDF report downloaded.", "success");
      } catch (err) {
        if (App) App.showToast(err.message || "PDF download failed.", "error");
      }
    }
  
    async function downloadExcel() {
      if (!window.App || !App.hasConfiguredBackend()) {
        if (App) App.showToast("Backend required for Excel reports.", "warn"); return;
      }
      if (App) App.showToast("Generating Excel report...", "info");
      try {
        const params = getFilterParams();
        const query  = Object.entries(params)
          .filter(([,v]) => v && v !== "All")
          .map(([k,v]) => k + "=" + encodeURIComponent(v)).join("&");
        const url = App.buildApiUrl("/api/reports/excel") + (query ? "?" + query : "");
        const token = localStorage.getItem("sales_auth_token") || "";
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Authorization": "Bearer " + token }
        });
        if (!resp.ok) throw new Error("Report generation failed.");
        const blob = await resp.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${slugify(state.meta.datasetName || (isSalesMode() ? "sales-report" : "dataset-report"))}.xlsx`;
        a.click();
        URL.revokeObjectURL(a.href);
        if (App) App.showToast("Excel report downloaded.", "success");
      } catch (err) {
        if (App) App.showToast(err.message || "Excel download failed.", "error");
      }
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       EMAIL SCHEDULER MODAL
    ═══════════════════════════════════════════════════════════════════════ */
    function toggleEmailModal() {
      const modal = document.getElementById("emailModal");
      if (!modal) return;
      const isOpen = modal.classList.toggle("open");
      if (isOpen) {
        loadEmailStatus();
        loadEmailSchedules();
      }
    }

    async function loadEmailStatus() {
      const note = document.getElementById("emailStatusNote");
      if (!note || !window.App || !App.hasConfiguredBackend()) return;
      note.textContent = "Checking email status...";
      note.style.color = "var(--text-hint)";
      try {
        const status = await App.request("/api/email/status");
        note.textContent = status.message || "Email status available.";
        note.style.color = status.enabled ? "#4ADE80" : "#FBBF24";
      } catch (e) {
        note.textContent = (e && e.message) || "Could not read email status.";
        note.style.color = "#F87171";
      }
    }
  
    async function loadEmailSchedules() {
      if (!window.App || !App.hasConfiguredBackend()) return;
      const listEl = document.getElementById("emailScheduleList");
      if (!listEl) return;
      listEl.innerHTML = '<div style="color:var(--text-hint);font-size:12px;padding:8px 0;">Loading...</div>';
      try {
        const schedules = await App.request("/api/email/schedules");
        if (!schedules.length) {
          listEl.innerHTML = '<div style="color:var(--text-hint);font-size:12px;padding:8px 0;">No active schedules.</div>';
          return;
        }
        listEl.innerHTML = schedules.map(s => `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--glass-border);">
            <div>
              <div style="font-size:12px;font-weight:600;color:var(--white);">${esc(s.recipient_email||s.recipients?.[0]||"")}</div>
              <div style="font-size:10px;color:var(--text-hint);">${esc(s.frequency||"")} · ${esc(s.report_type||s.report_format||"")}</div>
            </div>
            <button onclick="deleteSchedule(${s.id||JSON.stringify(s.id)})" style="background:rgba(220,38,38,0.12);border:1px solid rgba(220,38,38,0.3);color:#F87171;border-radius:5px;padding:4px 10px;font-size:10px;font-weight:600;cursor:pointer;font-family:inherit;">Remove</button>
          </div>`).join("");
      } catch (e) {
        const msg = (e && e.message) || "Could not load schedules.";
        listEl.innerHTML = `<div style="color:var(--text-hint);font-size:12px;">${esc(msg)}</div>`;
        if (App) App.showToast(msg, "warn");
      }
    }
  
    async function createEmailSchedule() {
      if (!window.App || !App.hasConfiguredBackend()) {
        if (App) App.showToast("Backend required.", "warn"); return;
      }
      const email  = val("scheduleEmail");
      const freq   = val("scheduleFreq");
      const format = val("scheduleFormat");
      const time   = val("scheduleTime") || "09:00";
      if (!email) { if (App) App.showToast("Enter recipient email.", "warn"); return; }
      try {
        await App.request("/api/email/schedules", {
          method: "POST",
          body: {
            recipient_email: email,
            subject: "Zero Click AI — Scheduled Sales Report",
            frequency: freq,
            schedule_time: time,
            report_type: format,
            filters: getFilterParams()
          }
        });
        if (App) App.showToast("Schedule created. First report sending now.", "success");
        loadEmailSchedules();
      } catch (err) {
        if (App) App.showToast(err.message || "Could not create schedule.", "error");
      }
    }
  
    async function deleteSchedule(id) {
      if (!id) return;
      try {
        await App.request(`/api/email/schedules/${id}`, { method: "DELETE" });
        if (App) App.showToast("Schedule removed.", "success");
        loadEmailSchedules();
      } catch (err) {
        if (App) App.showToast(err.message || "Could not remove schedule.", "error");
      }
    }
  
    async function sendReportNow() {
      if (!window.App || !App.hasConfiguredBackend()) {
        if (App) App.showToast("Backend required.", "warn"); return;
      }
      const email  = val("scheduleEmail");
      const format = val("scheduleFormat") || "excel";
      if (!email) { if (App) App.showToast("Enter recipient email first.", "warn"); return; }
      try {
        await App.request("/api/email/send-now", {
          method: "POST",
          body: {
            recipient_email: email,
            subject: "Zero Click AI — Sales Report",
            frequency: "Daily",
            report_type: format,
            filters: getFilterParams()
          }
        });
        if (App) App.showToast("Report sending to " + email + ".", "success");
      } catch (err) {
        if (App) App.showToast(err.message || "Could not send report.", "error");
      }
    }
  
    function exportFilteredCsv() {
      const rows = state.tableRows && state.tableRows.length ? state.tableRows : state.filtered;
      if (!rows.length) { if (App) App.showToast("No filtered data to export.", "error"); return; }
      const columns = Object.keys(rows[0]);
      const csv = [
        columns.join(","),
        ...rows.map(r => columns.map(col => csvCell(r[col])).join(","))
      ].join("\n");
      downloadBlob(csv, `${slugify(state.meta.datasetName || "filtered-dataset")}.csv`, "text/csv;charset=utf-8");
    }
  
    function exportSummaryJson() {
      const summary = {
        mode: state.meta.mode||"demo", dataset:state.meta.datasetName||"Dataset",
        updatedAt:state.meta.updatedAt||new Date().toISOString(),
        filters:getFilterParams(), rows:state.filtered.length,
        datasetType: state.meta.datasetType || "generic",
        targetColumn: state.meta.targetColumn || null,
        dateColumn: state.meta.dateColumn || null,
        warnings: state.meta.warnings || [],
        recommendations: state.recommendations || []
      };
      downloadBlob(JSON.stringify(summary,null,2),"dashboard-summary.json","application/json");
    }
  
    function downloadBlob(content, name, type) {
      const blob = new Blob([content],{type});
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href=url; a.download=name;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       SIDEBAR TOGGLE
    ═══════════════════════════════════════════════════════════════════════ */
    function toggleSidebar() {
      const sb   = document.getElementById("mainSidebar");
      const main = document.querySelector(".main");
      const btn  = document.getElementById("sidebarToggleBtn");
      const col  = sb ? sb.classList.toggle("collapsed") : false;
      if (main) main.classList.toggle("collapsed", col);
      if (btn) {
        const icon = btn.querySelector(".sb-toggle-icon");
        if (icon) icon.style.transform = col ? "rotate(180deg)" : "rotate(0deg)";
      }
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       BACKEND CONFIG
    ═══════════════════════════════════════════════════════════════════════ */
    function configureBackend() {
      // Auto-connected via app.js origin detection
      if (App) App.showToast("Backend auto-connected to " + App.getApiBase(), "success");
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       SIGN OUT
    ═══════════════════════════════════════════════════════════════════════ */
    function signOut() {
      if (window.App) App.signOut();
      else {
        ["isLoggedIn","userEmail","userRole"].forEach(k => localStorage.removeItem(k));
        window.location.href = "login.html";
      }
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       STORAGE HELPERS
    ═══════════════════════════════════════════════════════════════════════ */
    function getStoredRows() {
      try { return JSON.parse(localStorage.getItem(STORAGE.rows)) || DEMO_ROWS; } catch(e) { return DEMO_ROWS; }
    }
    function getStoredMeta() {
      try { return JSON.parse(localStorage.getItem(STORAGE.meta)) || {}; } catch(e) { return {}; }
    }
  
    /* ═══════════════════════════════════════════════════════════════════════
       UTILITIES
    ═══════════════════════════════════════════════════════════════════════ */
    function monthlySeries(rows) {
      return { labels:MONTHS, values:MONTHS.map((_,i) => rows.filter(r => r.month===i+1).reduce((s,r) => s+r.sales,0)) };
    }
    function buildScatterSeries(rows) {
      const safeRows = Array.isArray(rows) ? rows : [];
      const sample = safeRows.slice(0, 120);
      const points = sample
        .filter(r => Number.isFinite(Number(r.sales)) && Number.isFinite(Number(r.profit)))
        .map(r => ({ x: Number(r.sales), y: Number(r.profit) }));
      return {
        labels: sample.map(r => `${r.product || "Item"} (${r.region || "Region"})`),
        points: points.length ? points : [{ x: 0, y: 0 }]
      };
    }
    function buildHeatmapSeries(rows) {
      const safeRows = Array.isArray(rows) ? rows : [];
      const regionList = unique(safeRows.map(r => r.region)).slice(0, 8);
      const monthList = MONTHS.slice();
      const regionIndex = Object.fromEntries(regionList.map((r, i) => [r, i]));
      const cellMap = {};
      safeRows.forEach(r => {
        const ri = regionIndex[r.region];
        const mi = Math.max(0, Math.min(11, (Number(r.month) || 1) - 1));
        if (ri === undefined) return;
        const key = `${ri}-${mi}`;
        cellMap[key] = (cellMap[key] || 0) + Number(r.sales || 0);
      });
      const points = [];
      Object.entries(cellMap).forEach(([key, value]) => {
        const [ri, mi] = key.split("-").map(Number);
        points.push({ x: mi, y: ri, v: value });
      });
      if (!points.length) points.push({ x: 0, y: 0, v: 0 });
      return {
        xLabels: monthList,
        yLabels: regionList.length ? regionList : ["No region"],
        points
      };
    }
    function detectTargetMetric() {
      const preferred = String(state.meta.targetColumn || "").toLowerCase();
      if (preferred.includes("profit")) return "profit";
      if (preferred.includes("quantity") || preferred.includes("qty")) return "qty";
      if (preferred.includes("discount")) return "disc";
      if (preferred.includes("sales") || preferred.includes("revenue") || preferred.includes("amount")) return "sales";
      return isSalesMode() ? "sales" : "qty";
    }
    function metricLabelFor(key) {
      return ({ sales: "Sales", profit: "Profit", qty: "Quantity", disc: "Discount" }[key]) || primaryMetricLabel();
    }
    function formatMetricValue(key, value) {
      if (key === "disc") return `${Number(value || 0).toFixed(1)}%`;
      if (key === "sales" || key === "profit") return money(value);
      return Number(value || 0).toLocaleString("en-US", { maximumFractionDigits: 2 });
    }
    function showLoader(message) {
      state.loaderCount += 1;
      let overlay = document.getElementById("appLoaderOverlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "appLoaderOverlay";
        overlay.className = "app-loader-overlay";
        overlay.innerHTML = '<div class="app-loader-card"><div class="app-loader-spinner"></div><div class="app-loader-text" id="appLoaderText">Loading...</div></div>';
        document.body.appendChild(overlay);
      }
      const text = document.getElementById("appLoaderText");
      if (text) text.textContent = message || "Loading...";
      overlay.style.display = "flex";
    }
    function hideLoader() {
      state.loaderCount = Math.max(0, state.loaderCount - 1);
      if (state.loaderCount > 0) return;
      const overlay = document.getElementById("appLoaderOverlay");
      if (overlay) overlay.style.display = "none";
    }
    function aggregate(rows, key, metric) {
      const t={};
      rows.forEach(r => { t[r[key]]=(t[r[key]]||0)+Number(r[metric]||0); });
      return Object.entries(t).map(([label,value])=>({label,value})).sort((a,b)=>b.value-a.value);
    }
    function sum(rows, key)    { return rows.reduce((s,r) => s+Number(r[key]||0), 0); }
    function unique(vals)      { return Array.from(new Set(vals.filter(v => v!==undefined&&v!==null&&v!==""))); }
    function money(v)          { return `${v<0?"-":""}$${Math.abs(Number(v||0)).toLocaleString("en-US",{maximumFractionDigits:0})}`; }
    function moneyCompact(v)   { return new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",notation:"compact",maximumFractionDigits:1}).format(Number(v||0)); }
    function numberCompact(v)  { return new Intl.NumberFormat("en-US",{notation:"compact",maximumFractionDigits:1}).format(Number(v||0)); }
    function card(l,v,s)       { return {label:l,value:v,sub:s}; }
    function number(v)         { const n=Number(String(v||"").replace(/[^0-9.-]/g,"")); return isFinite(n)?n:0; }
    function text(v,fb)        { const t=String(v||"").trim(); return t||fb; }
    function pick(lk,keys)     { return keys.map(k=>lk[k]).find(v=>v!==undefined&&v!==""); }
    function esc(v)            { return String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
    function csvCell(v)        { return `"${String(v).replace(/"/g,'""')}"`; }
    function slugify(v)        { return String(v||"dataset").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"") || "dataset"; }
    function val(id)           { const el=document.getElementById(id); return el?el.value:"All"; }
    function safe(id,fn)       { const el=document.getElementById(id); if(el) fn(el); }
    function formatDate(v)     { try { return new Date(v).toLocaleString("en-IN",{dateStyle:"medium",timeStyle:"short"}); } catch(e){ return "Not available"; } }
    function monthLabel(k)     { const p=String(k).split("-"); return p.length===2?`${MONTHS[Number(p[1])-1]} ${p[0]}`:k; }
    function formatCell(col, value) {
      if (value === null || value === undefined || value === "") return "";
      if (typeof value === "number") {
        if (isSalesMode() && /sales|revenue|profit|amount|total/i.test(col)) return money(value);
        return Number(value).toLocaleString("en-US", { maximumFractionDigits: 2 });
      }
      const num = Number(value);
      if (!Number.isNaN(num) && String(value).trim() !== "") {
        if (isSalesMode() && /sales|revenue|profit|amount|total/i.test(col)) return money(num);
        return num.toLocaleString("en-US", { maximumFractionDigits: 2 });
      }
      return esc(value);
    }
  
    /* ── Expose globals ── */
    window.toggleSidebar     = toggleSidebar;
    window.downloadPDF          = downloadPDF;
    window.downloadExcel        = downloadExcel;
    window.toggleEmailModal     = toggleEmailModal;
    window.createEmailSchedule  = createEmailSchedule;
    window.deleteSchedule       = deleteSchedule;
    window.sendReportNow        = sendReportNow;
    window.toggleChat    = toggleChat;
    window.quickAsk      = quickAsk;
    window.sendMsg       = sendMsg;
    window.signOut       = signOut;
  })();

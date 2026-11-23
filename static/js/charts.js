window.UniCharts = {
  colors: ["#22b8cf", "#3b5bdb", "#845ef7", "#e8a317", "#e07a5f", "#2f9e44", "#748ffc"],
  defaults() {
    if (!window.Chart) return;
    Chart.defaults.font.family = "'Outfit', system-ui, sans-serif";
    Chart.defaults.color = "#5a7380";
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
  },
  parse(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  },
  doughnut(canvasId, dataId, label) {
    const data = this.parse(dataId);
    const ctx = document.getElementById(canvasId);
    if (!data || !ctx) return;
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.labels,
        datasets: [
          {
            data: data.data,
            backgroundColor: this.colors,
            borderWidth: 0,
            hoverOffset: 6,
          },
        ],
      },
      options: {
        cutout: "68%",
        plugins: {
          legend: { position: "bottom" },
          title: label ? { display: false } : undefined,
        },
        maintainAspectRatio: false,
      },
    });
  },
  bar(canvasId, dataId, opts = {}) {
    const data = this.parse(dataId);
    const ctx = document.getElementById(canvasId);
    if (!data || !ctx) return;
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: opts.label || "Valeur",
            data: data.data,
            backgroundColor: opts.color || "rgba(59, 91, 219, 0.75)",
            borderRadius: 10,
            maxBarThickness: 36,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            max: opts.max,
            grid: { color: "rgba(11,31,42,0.06)" },
          },
        },
        plugins: { legend: { display: !!opts.showLegend } },
      },
    });
  },
  line(canvasId, dataId, opts = {}) {
    const data = this.parse(dataId);
    const ctx = document.getElementById(canvasId);
    if (!data || !ctx) return;
    new Chart(ctx, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: opts.label || "Série",
            data: data.data,
            borderColor: opts.color || "#3b5bdb",
            backgroundColor: opts.fill || "rgba(59, 91, 219, 0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointHoverRadius: 5,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            max: opts.max,
            grid: { color: "rgba(11,31,42,0.06)" },
          },
        },
        plugins: { legend: { display: false } },
      },
    });
  },
};
document.addEventListener("DOMContentLoaded", () => UniCharts.defaults());

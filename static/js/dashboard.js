(function () {
  function getChartData(canvas) {
    try {
      return JSON.parse(canvas.dataset.chart || '[]');
    } catch (error) {
      return [];
    }
  }

  function setupCanvas(canvas) {
    var ctx = canvas.getContext('2d');
    var width = canvas.clientWidth || 320;
    var height = canvas.clientHeight || 240;
    var ratio = window.devicePixelRatio || 1;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    return { ctx: ctx, width: width, height: height };
  }

  function drawEmpty(ctx) {
    ctx.fillStyle = '#8a96a8';
    ctx.font = '13px Inter, sans-serif';
    ctx.fillText('Aucune donnee', 18, 32);
  }

  function drawGrid(ctx, width, height, padding) {
    ctx.strokeStyle = '#edf2f7';
    ctx.lineWidth = 1;
    for (var i = 0; i <= 5; i += 1) {
      var y = padding.top + ((height - padding.top - padding.bottom) / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();
    }
  }

  function drawArea(canvas, data) {
    var setup = setupCanvas(canvas);
    var ctx = setup.ctx;
    var width = setup.width;
    var height = setup.height;
    var padding = { top: 22, right: 18, bottom: 28, left: 38 };

    if (!data.length) {
      drawEmpty(ctx);
      return;
    }

    drawGrid(ctx, width, height, padding);

    var values = data.map(function (item) { return Number(item.value) || 0; });
    var max = Math.max.apply(null, values) || 1;
    var plotW = width - padding.left - padding.right;
    var plotH = height - padding.top - padding.bottom;
    var points = values.map(function (value, index) {
      var x = padding.left + (plotW / Math.max(values.length - 1, 1)) * index;
      var y = padding.top + plotH - (plotH * value / max);
      return { x: x, y: y, value: value, label: data[index].label };
    });

    var gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, 'rgba(66, 165, 245, 0.42)');
    gradient.addColorStop(1, 'rgba(66, 165, 245, 0.05)');

    ctx.beginPath();
    ctx.moveTo(points[0].x, height - padding.bottom);
    points.forEach(function (point) { ctx.lineTo(point.x, point.y); });
    ctx.lineTo(points[points.length - 1].x, height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    points.forEach(function (point, index) {
      if (index === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    });
    ctx.strokeStyle = '#42a5f5';
    ctx.lineWidth = 3;
    ctx.stroke();

    points.forEach(function (point, index) {
      if (index % 2 !== 0 && points.length > 6) return;
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#42a5f5';
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    ctx.fillStyle = '#8a96a8';
    ctx.font = '11px Inter, sans-serif';
    points.forEach(function (point, index) {
      if (index % 2 !== 0 && points.length > 6) return;
      ctx.fillText(point.label.split(' ')[0], point.x - 12, height - 8);
    });
  }

  function drawBars(canvas, data) {
    var setup = setupCanvas(canvas);
    var ctx = setup.ctx;
    var width = setup.width;
    var height = setup.height;
    var padding = { top: 18, right: 16, bottom: 24, left: 18 };

    if (!data.length) {
      drawEmpty(ctx);
      return;
    }

    var max = Math.max.apply(null, data.map(function (item) { return Number(item.value) || 0; })) || 1;
    var plotW = width - padding.left - padding.right;
    var plotH = height - padding.top - padding.bottom;
    var gap = 8;
    var barW = Math.max(12, (plotW - gap * (data.length - 1)) / data.length);

    data.forEach(function (item, index) {
      var value = Number(item.value) || 0;
      var barH = plotH * value / max;
      var x = padding.left + index * (barW + gap);
      var y = padding.top + plotH - barH;
      ctx.fillStyle = 'rgba(255,255,255,.86)';
      ctx.fillRect(x, y, barW, barH);
      ctx.fillStyle = 'rgba(255,255,255,.72)';
      ctx.font = '10px Inter, sans-serif';
      ctx.fillText(String(value), x, Math.max(12, y - 5));
    });
  }

  function drawChart(canvas) {
    var data = getChartData(canvas);
    if (canvas.dataset.variant === 'bars') {
      drawBars(canvas, data);
    } else {
      drawArea(canvas, data);
    }
  }

  function drawAll() {
    document.querySelectorAll('.dashboard-chart').forEach(drawChart);
  }

  window.addEventListener('load', drawAll);
  window.addEventListener('resize', drawAll);
})();

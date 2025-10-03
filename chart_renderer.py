<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --text-primary: #333333;
            --text-secondary: #666666;
            --border-color: #e0e0e0;
            --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            --accent-color: #2196F3;
        }

        [data-theme="dark"] {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --border-color: #404040;
            --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
            --accent-color: #64B5F6;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        .header {
            background-color: var(--bg-primary);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--card-shadow);
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .theme-toggle {
            background: none;
            border: 2px solid var(--border-color);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            color: var(--text-primary);
            font-size: 0.9rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .theme-toggle:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
            transition: transform 0.2s ease;
        }

        .stat-card:hover {
            transform: translateY(-2px);
        }

        .stat-card h3 {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-color);
        }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .chart-card {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
            min-height: 400px;
        }

        .chart-card h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .chart-container {
            width: 100%;
            height: 300px;
            position: relative;
        }

        .full-width-chart {
            grid-column: 1 / -1;
        }

        @media (max-width: 768px) {
            .header {
                padding: 1rem;
            }

            .container {
                padding: 1rem;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .charts-grid {
                grid-template-columns: 1fr;
            }

            .chart-card {
                min-height: 300px;
            }

            .chart-container {
                height: 200px;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>Analytics Dashboard</h1>
        <button class="theme-toggle" id="themeToggle">
            <span id="themeIcon">🌙</span>
            <span id="themeText">Dark Mode</span>
        </button>
    </header>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Users</h3>
                <div class="value" id="totalUsers">12,345</div>
            </div>
            <div class="stat-card">
                <h3>Revenue</h3>
                <div class="value" id="revenue">$54,321</div>
            </div>
            <div class="stat-card">
                <h3>Active Sessions</h3>
                <div class="value" id="activeSessions">1,234</div>
            </div>
            <div class="stat-card">
                <h3>Conversion Rate</h3>
                <div class="value" id="conversionRate">3.2%</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <h2>User Growth</h2>
                <div class="chart-container">
                    <canvas id="chart1"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h2>Revenue Over Time</h2>
                <div class="chart-container">
                    <canvas id="chart2"></canvas>
                </div>
            </div>
            <div class="chart-card full-width-chart">
                <h2>Traffic Sources</h2>
                <div class="chart-container">
                    <canvas id="chart3"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h2>Device Distribution</h2>
                <div class="chart-container">
                    <canvas id="chart4"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h2>Top Performing Pages</h2>
                <div class="chart-container">
                    <canvas id="chart5"></canvas>
                </div>
            </div>
        </div>
    </div>

    <script>
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        const themeText = document.getElementById('themeText');
        const htmlElement = document.documentElement;

        const savedTheme = localStorage.getItem('theme') || 'light';
        htmlElement.setAttribute('data-theme', savedTheme);
        updateThemeButton(savedTheme);

        let charts = {};

        function getChartColors() {
            const isDark = htmlElement.getAttribute('data-theme') === 'dark';
            return {
                primary: isDark ? '#64B5F6' : '#2196F3',
                success: isDark ? '#81C784' : '#4CAF50',
                warning: isDark ? '#FFB74D' : '#FF9800',
                danger: isDark ? '#E57373' : '#F44336',
                info: isDark ? '#4DD0E1' : '#00BCD4',
                purple: isDark ? '#BA68C8' : '#9C27B0',
                text: isDark ? '#e0e0e0' : '#333333',
                grid: isDark ? '#404040' : '#e0e0e0',
                bg: isDark ? '#1a1a1a' : '#ffffff'
            };
        }

        function createChart1() {
            const colors = getChartColors();
            const ctx = document.getElementById('chart1').getContext(
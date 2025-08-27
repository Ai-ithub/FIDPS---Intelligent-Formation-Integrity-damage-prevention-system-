// FIDPS Dashboard JavaScript
// Real-time dashboard functionality with WebSocket connections

class FIDPSDashboard {
    constructor() {
        this.websocket = null;
        this.clientId = this.generateClientId();
        this.charts = {};
        this.currentTab = 'overview';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.init();
    }

    generateClientId() {
        return 'dashboard_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    init() {
        this.setupEventListeners();
        this.updateCurrentTime();
        this.connectWebSocket();
        this.initializeCharts();
        this.loadInitialData();
        
        // Update time every second
        setInterval(() => this.updateCurrentTime(), 1000);
        
        // Periodic data refresh
        setInterval(() => this.refreshCurrentTab(), 30000);
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(e.target.getAttribute('data-tab'));
            });
        });

        // Anomaly filter
        const anomalyFilter = document.getElementById('anomaly-filter');
        if (anomalyFilter) {
            anomalyFilter.addEventListener('change', () => this.filterAnomalies());
        }

        // Window visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }

    updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = timeString;
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/${this.clientId}`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
                this.reconnectAttempts = 0;
                
                // Subscribe to data streams
                this.subscribeToStreams();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus(false);
        }
    }

    subscribeToStreams() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            // Subscribe to all wells data
            this.websocket.send(JSON.stringify({
                type: 'subscribe',
                subscription: 'all_wells'
            }));
            
            // Subscribe to anomalies
            this.websocket.send(JSON.stringify({
                type: 'subscribe',
                subscription: 'anomalies'
            }));
            
            // Subscribe to system metrics
            this.websocket.send(JSON.stringify({
                type: 'subscribe',
                subscription: 'system_metrics'
            }));
        }
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'sensor_data_update':
                this.handleSensorDataUpdate(message);
                break;
            case 'anomaly_alert':
                this.handleAnomalyAlert(message);
                break;
            case 'system_status_update':
                this.handleSystemStatusUpdate(message);
                break;
            case 'subscription_confirmed':
                console.log(`Subscribed to ${message.subscription}`);
                break;
            case 'pong':
                // Handle ping/pong for connection keep-alive
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    handleSensorDataUpdate(message) {
        // Update real-time charts
        if (this.charts.sensorData && message.data) {
            this.updateSensorDataChart(message.data);
        }
        
        // Update well status if on wells tab
        if (this.currentTab === 'wells') {
            this.updateWellStatus(message.well_id, message.data);
        }
    }

    handleAnomalyAlert(message) {
        // Show notification
        this.showNotification('New Anomaly Alert', message.alert.description, 'warning');
        
        // Update anomaly count
        this.incrementAnomalyCount();
        
        // Update anomaly table if on anomalies tab
        if (this.currentTab === 'anomalies') {
            this.addAnomalyToTable(message.alert);
        }
        
        // Update charts
        if (this.charts.anomalyDistribution) {
            this.updateAnomalyDistributionChart();
        }
    }

    handleSystemStatusUpdate(message) {
        this.updateSystemStatus(message.status);
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            if (connected) {
                statusElement.className = 'connection-status connected';
                statusElement.innerHTML = '<i class="fas fa-wifi"></i> Connected';
            } else {
                statusElement.className = 'connection-status disconnected';
                statusElement.innerHTML = '<i class="fas fa-wifi"></i> Disconnected';
            }
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.showNotification('Connection Lost', 'Unable to reconnect to server', 'error');
        }
    }

    switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Show selected tab content
        const targetContent = document.getElementById(`${tabName}-content`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
        
        this.currentTab = tabName;
        this.loadTabData(tabName);
    }

    loadTabData(tabName) {
        switch (tabName) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'wells':
                this.loadWellsData();
                break;
            case 'anomalies':
                this.loadAnomaliesData();
                break;
            case 'data-quality':
                this.loadDataQualityData();
                break;
            case 'system':
                this.loadSystemData();
                break;
        }
    }

    async loadInitialData() {
        try {
            // Load dashboard overview
            const response = await fetch('/api/v1/dashboard/overview');
            if (response.ok) {
                const data = await response.json();
                this.updateOverviewMetrics(data);
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    async loadOverviewData() {
        try {
            // Load overview metrics
            const overviewResponse = await fetch('/api/v1/dashboard/overview');
            if (overviewResponse.ok) {
                const overviewData = await overviewResponse.json();
                this.updateOverviewMetrics(overviewData);
            }
            
            // Load recent alerts
            const alertsResponse = await fetch('/api/v1/anomalies/active?limit=10');
            if (alertsResponse.ok) {
                const alertsData = await alertsResponse.json();
                this.updateRecentAlerts(alertsData);
            }
        } catch (error) {
            console.error('Error loading overview data:', error);
        }
    }

    async loadWellsData() {
        try {
            const response = await fetch('/api/v1/wells');
            if (response.ok) {
                const data = await response.json();
                this.updateWellsDisplay(data.wells);
            }
        } catch (error) {
            console.error('Error loading wells data:', error);
        }
    }

    async loadAnomaliesData() {
        try {
            const filter = document.getElementById('anomaly-filter')?.value || '';
            const url = filter ? `/api/v1/anomalies/active?severity=${filter}` : '/api/v1/anomalies/active';
            
            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                this.updateAnomaliesTable(data);
            }
        } catch (error) {
            console.error('Error loading anomalies data:', error);
        }
    }

    async loadDataQualityData() {
        try {
            const response = await fetch('/api/v1/validation/results?limit=50');
            if (response.ok) {
                const data = await response.json();
                this.updateDataQualityDisplay(data);
            }
        } catch (error) {
            console.error('Error loading data quality data:', error);
        }
    }

    async loadSystemData() {
        try {
            const response = await fetch('/api/v1/system/status');
            if (response.ok) {
                const data = await response.json();
                this.updateSystemStatusDisplay(data);
            }
        } catch (error) {
            console.error('Error loading system data:', error);
        }
    }

    updateOverviewMetrics(data) {
        // Update metric cards
        this.updateElement('active-wells-count', data.active_wells || 0);
        this.updateElement('anomalies-today-count', data.total_anomalies_today || 0);
        this.updateElement('critical-alerts-count', data.critical_alerts || 0);
        this.updateElement('data-quality-score', `${(data.data_quality_score || 0).toFixed(1)}%`);
        
        // Update system status
        this.updateSystemStatus(data.system_health || 'unknown');
    }

    updateSystemStatus(status) {
        const indicator = document.getElementById('system-status-indicator');
        const text = document.getElementById('system-status-text');
        
        if (indicator && text) {
            // Remove existing status classes
            indicator.className = 'status-indicator';
            
            switch (status) {
                case 'healthy':
                    indicator.classList.add('status-healthy');
                    text.textContent = 'Healthy';
                    break;
                case 'warning':
                    indicator.classList.add('status-warning');
                    text.textContent = 'Warning';
                    break;
                case 'degraded':
                case 'unhealthy':
                    indicator.classList.add('status-critical');
                    text.textContent = 'Critical';
                    break;
                default:
                    indicator.classList.add('status-unknown');
                    text.textContent = 'Unknown';
            }
        }
    }

    updateRecentAlerts(alerts) {
        const container = document.getElementById('recent-alerts-container');
        if (!container) return;
        
        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">No recent alerts</p>';
            return;
        }
        
        const alertsHtml = alerts.map(alert => {
            const severityClass = `alert-${alert.severity}`;
            const timeAgo = this.getTimeAgo(new Date(alert.timestamp));
            
            return `
                <div class="alert alert-light ${severityClass} alert-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${alert.well_id}</strong> - ${alert.anomaly_type}
                            <p class="mb-1">${alert.description}</p>
                            <small class="text-muted">${timeAgo}</small>
                        </div>
                        <span class="badge bg-${this.getSeverityColor(alert.severity)}">
                            ${alert.severity.toUpperCase()}
                        </span>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = alertsHtml;
    }

    updateWellsDisplay(wells) {
        const container = document.getElementById('wells-container');
        if (!container) return;
        
        if (wells.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">No wells found</p>';
            return;
        }
        
        const wellsHtml = wells.map(well => {
            const statusClass = well.is_active ? 'well-active' : 'well-inactive';
            const statusText = well.is_active ? 'Active' : 'Inactive';
            const statusIcon = well.is_active ? 'fa-circle text-success' : 'fa-circle text-secondary';
            
            return `
                <div class="well-card ${statusClass}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">
                                <i class="fas ${statusIcon} me-2"></i>
                                ${well.well_id}
                            </h6>
                            <p class="mb-1 text-muted">Last Data: ${new Date(well.last_data_time).toLocaleString()}</p>
                            <small class="text-muted">${well.data_points.toLocaleString()} data points</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${well.is_active ? 'success' : 'secondary'}">
                                ${statusText}
                            </span>
                            <br>
                            <small class="text-muted">Depth: ${well.max_depth?.toFixed(1) || 'N/A'}m</small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = wellsHtml;
    }

    updateAnomaliesTable(anomalies) {
        const tbody = document.getElementById('anomalies-table-body');
        if (!tbody) return;
        
        if (anomalies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">No anomalies found</td></tr>';
            return;
        }
        
        const rowsHtml = anomalies.map(anomaly => {
            const severityColor = this.getSeverityColor(anomaly.severity);
            const statusBadge = anomaly.status === 'active' ? 'danger' : 'secondary';
            
            return `
                <tr>
                    <td>${new Date(anomaly.timestamp).toLocaleString()}</td>
                    <td>${anomaly.well_id}</td>
                    <td>${anomaly.anomaly_type}</td>
                    <td><span class="badge bg-${severityColor}">${anomaly.severity.toUpperCase()}</span></td>
                    <td>${anomaly.description}</td>
                    <td><span class="badge bg-${statusBadge}">${anomaly.status.toUpperCase()}</span></td>
                    <td>
                        ${anomaly.status === 'active' ? 
                            `<button class="btn btn-acknowledge btn-sm" onclick="acknowledgeAnomaly('${anomaly.id}')">
                                <i class="fas fa-check me-1"></i>Acknowledge
                            </button>` : 
                            '<span class="text-muted">-</span>'
                        }
                    </td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = rowsHtml;
    }

    initializeCharts() {
        this.initializeSensorDataChart();
        this.initializeAnomalyDistributionChart();
        this.initializeDataQualityChart();
    }

    initializeSensorDataChart() {
        const ctx = document.getElementById('sensor-data-chart');
        if (!ctx) return;
        
        this.charts.sensorData = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Pressure (psi)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Temperature (°F)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute'
                        }
                    },
                    y: {
                        beginAtZero: false
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    initializeAnomalyDistributionChart() {
        const ctx = document.getElementById('anomaly-distribution-chart');
        if (!ctx) return;
        
        this.charts.anomalyDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'Warning', 'Info'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgb(220, 53, 69)',
                        'rgb(255, 193, 7)',
                        'rgb(13, 202, 240)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initializeDataQualityChart() {
        const ctx = document.getElementById('data-quality-chart');
        if (!ctx) return;
        
        this.charts.dataQuality = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Data Quality Score (%)',
                    data: [],
                    borderColor: 'rgb(40, 167, 69)',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Utility functions
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    getSeverityColor(severity) {
        switch (severity) {
            case 'critical': return 'danger';
            case 'warning': return 'warning';
            case 'info': return 'info';
            default: return 'secondary';
        }
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    showNotification(title, message, type = 'info') {
        // Simple notification system
        console.log(`${type.toUpperCase()}: ${title} - ${message}`);
        
        // You can implement a more sophisticated notification system here
        // For now, we'll use browser notifications if available
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/favicon.ico'
            });
        }
    }

    refreshCurrentTab() {
        this.loadTabData(this.currentTab);
    }

    pauseUpdates() {
        // Pause real-time updates when tab is not visible
        if (this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'pause_updates'
            }));
        }
    }

    resumeUpdates() {
        // Resume real-time updates when tab becomes visible
        if (this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'resume_updates'
            }));
        }
        this.refreshCurrentTab();
    }
}

// Global functions
function refreshWells() {
    dashboard.loadWellsData();
}

function refreshAnomalies() {
    dashboard.loadAnomaliesData();
}

function refreshDataQuality() {
    dashboard.loadDataQualityData();
}

function refreshSystemStatus() {
    dashboard.loadSystemData();
}

async function acknowledgeAnomaly(anomalyId) {
    try {
        const response = await fetch(`/api/v1/anomalies/${anomalyId}/acknowledge`, {
            method: 'POST'
        });
        
        if (response.ok) {
            dashboard.showNotification('Success', 'Anomaly acknowledged', 'success');
            dashboard.loadAnomaliesData();
        } else {
            dashboard.showNotification('Error', 'Failed to acknowledge anomaly', 'error');
        }
    } catch (error) {
        console.error('Error acknowledging anomaly:', error);
        dashboard.showNotification('Error', 'Failed to acknowledge anomaly', 'error');
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new FIDPSDashboard();
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});
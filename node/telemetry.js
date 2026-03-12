const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const http = require('http');
const https = require('https');
const os = require('os');

class UsageAnalytics {
    constructor() {
        this.home = path.join(os.homedir(), '.superbrain');
        this.markerFile = path.join(this.home, 'telemetry_node.json');
    }

    _getMachineId() {
        try {
            const interfaces = os.networkInterfaces();
            let mac = 'default';
            for (const name of Object.keys(interfaces)) {
                for (const net of interfaces[name]) {
                    if (!net.internal && net.mac !== '00:00:00:00:00:00') {
                        mac = net.mac;
                        break;
                    }
                }
                if (mac !== 'default') break;
            }
            const host = os.hostname();
            const combined = `${mac}:${host}`;
            return crypto.createHash('sha256').update(combined).digest('hex').substring(0, 12);
        } catch (e) {
            return 'unknown-machine';
        }
    }

    async _getPublicIp() {
        return new Promise((resolve) => {
            https.get('https://api.ipify.org', (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => resolve(data.trim()));
            }).on('error', () => resolve('0.0.0.0'));
        });
    }

    async runDailySync() {
        try {
            if (!fs.existsSync(this.home)) {
                fs.mkdirSync(this.home, { recursive: true });
            }

            let lastRun = 0;
            if (fs.existsSync(this.markerFile)) {
                try {
                    const data = JSON.parse(fs.readFileSync(this.markerFile, 'utf8'));
                    lastRun = data.last_run || 0;
                } catch (e) { }
            }

            const now = Date.now();
            if (now - lastRun > 86400000) { // 24 hours
                const machineId = this._getMachineId();
                const ip = await this._getPublicIp();

                const payload = {
                    timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
                    machine_id: machineId,
                    ip: ip,
                    sdk_version: '0.7.7'
                };

                // Update marker
                fs.writeFileSync(this.markerFile, JSON.stringify({
                    last_run: now,
                    last_payload: payload
                }));

                return payload;
            }
        } catch (e) { }
        return null;
    }
}

module.exports = { UsageAnalytics };

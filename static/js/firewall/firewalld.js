// ===== FIREWALLD FIREWALL JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    // Sayfa yüklendiğinde firewalld durumunu ve kurallarını yükle
    loadFirewalldStatus();
    loadFirewalldRules();
    
    // Event listeners
    document.getElementById('refreshFirewalld').addEventListener('click', function() {
        loadFirewalldStatus();
        loadFirewalldRules();
    });
    
    document.getElementById('toggleFirewalld').addEventListener('click', function() {
        toggleFirewalld();
    });
    
    // Otomatik status kontrolü (her 5 saniyede bir)
    setInterval(function() {
        checkFirewalldStatus();
    }, 5000);
    
    // Sayfa focus olduğunda status kontrolü
    window.addEventListener('focus', function() {
        loadFirewalldStatus();
    });
    
    // Sayfa görünür olduğunda status kontrolü
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            loadFirewalldStatus();
        }
    });
});

// ===== FIREWALLD DURUM YÜKLEME =====
function loadFirewalldStatus() {
    const statusIndicator = document.getElementById('firewalldStatusIndicator');
    const toggleBtn = document.getElementById('toggleFirewalld');
    const toggleText = document.getElementById('toggleText');
    
    if (!statusIndicator || !toggleBtn || !toggleText) return;
    
    // Loading durumu
    statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.checking || 'Checking...';
    statusIndicator.querySelector('.status-dot').className = 'status-dot';
    
    fetch('/firewall/firewalld/api/status/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('firewalld Status API Response:', data);
            if (data.success && data.available) {
                if (data.status === 'active') {
                    statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.enabled || 'Active';
                    statusIndicator.querySelector('.status-text').className = 'status-text active';
                    statusIndicator.querySelector('.status-dot').className = 'status-dot active';
                    toggleText.textContent = window.jsTranslations.disable || 'Disable';
                    toggleBtn.className = 'btn-toggle active';
                    toggleBtn.disabled = false;
                    
                    // firewalld aktifse kuralları yükle
                    loadFirewalldRules();
                } else {
                    statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.disabled || 'Inactive';
                    statusIndicator.querySelector('.status-text').className = 'status-text inactive';
                    statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
                    toggleText.textContent = window.jsTranslations.enable || 'Enable';
                    toggleBtn.className = 'btn-toggle';
                    toggleBtn.disabled = false;
                    
                    // firewalld kapalıysa kuralları yükle
                    loadFirewalldRules();
                }
            } else {
                statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.not_available || 'Not Available';
                statusIndicator.querySelector('.status-text').className = 'status-text inactive';
                statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
                toggleBtn.disabled = true;
                toggleText.textContent = window.jsTranslations.not_available || 'Not Available';
                
                // firewalld mevcut değilse boş durum göster
                displayFirewalldUnavailable();
            }
        })
        .catch(error => {
            console.error('Error loading firewalld status:', error);
            statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.error || 'Error';
            statusIndicator.querySelector('.status-text').className = 'status-text inactive';
            statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
            toggleBtn.disabled = true;
            toggleText.textContent = window.jsTranslations.error || 'Error';
            
            // Hata durumunda boş durum göster
            displayFirewalldUnavailable();
        });
}

// ===== FIREWALLD KURALLARI YÜKLEME =====
function loadFirewalldRules() {
    const rulesLoading = document.getElementById('firewalldRulesLoading');
    const rulesContainer = document.getElementById('firewalldRulesContainer');
    const rulesEmpty = document.getElementById('firewalldRulesEmpty');
    const rulesCount = document.getElementById('rulesCount');
    
    if (!rulesLoading || !rulesContainer || !rulesEmpty || !rulesCount) return;
    
    // Önce firewalld status'unu kontrol et
    fetch('/firewall/firewalld/api/status/')
        .then(response => response.json())
        .then(statusData => {
            // firewalld mevcut değilse mesaj göster
            if (!statusData.available) {
                displayFirewalldUnavailable();
                rulesCount.textContent = '(0)';
                return;
            }
            
            // firewalld aktifse kuralları yükle
            rulesLoading.style.display = 'flex';
            rulesContainer.style.display = 'none';
            rulesEmpty.style.display = 'none';
            rulesCount.textContent = '(0)';
            
            return fetch('/firewall/firewalld/api/rules/');
        })
        .then(response => {
            if (!response) return; // firewalld mevcut değilse response yok
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data) return; // firewalld mevcut değilse data yok
            
            rulesLoading.style.display = 'none';
            
            console.log('firewalld Rules API Response:', data);
            
            if (data.success && data.rules) {
                console.log('firewalld Rules Output:', data.rules);
                console.log('firewalld Permanent Rules Output:', data.permanent_rules || 'N/A');
                
                // Runtime ve permanent kuralları parse et
                const runtimeZones = parseFirewalldRules(data.rules);
                const permanentZones = data.permanent_rules ? parseFirewalldRules(data.permanent_rules) : [];
                
                // Geçici/kalıcı ayırımı yap
                const zones = markTemporaryRules(runtimeZones, permanentZones);
                console.log('Parsed Zones (with temporary marking):', zones);
                
                if (zones.length > 0) {
                    const totalRules = zones.reduce((sum, zone) => sum + zone.totalRules, 0);
                    console.log('Total Rules:', totalRules);
                    
                    if (totalRules > 0) {
                        displayFirewalldRules(zones);
                        rulesContainer.style.display = 'block';
                        rulesEmpty.style.display = 'none';
                        rulesCount.textContent = `(${totalRules})`;
                    } else {
                        console.log('No rules found in zones');
                        showEmptyState();
                        rulesCount.textContent = '(0)';
                    }
                } else {
                    console.log('No zones found');
                    showEmptyState();
                    rulesCount.textContent = '(0)';
                }
            } else {
                console.error('API Error:', data.error || 'Unknown error');
                showEmptyState();
                rulesCount.textContent = '(0)';
            }
        })
        .catch(error => {
            console.error('Error loading firewalld rules:', error);
            rulesLoading.style.display = 'none';
            showEmptyState();
            rulesCount.textContent = '(0)';
        });
}

// ===== FIREWALLD KURALLARI PARSE ETME =====
function parseFirewalldRules(rulesOutput) {
    const lines = rulesOutput.split('\n');
    const zones = [];
    let currentZone = null;
    let ruleNumber = 1;
    
    console.log('firewalld Rules Output:', rulesOutput);
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Skip empty lines
        if (!line) continue;
        
        // Zone başlığı: "public (default, active)" veya "public (active)" veya "public"
        // Format: zone_name (optional_info, status) veya zone_name (status) veya zone_name
        const zoneMatch = line.match(/^(\w+)(?:\s+\([^)]+\))?$/);
        if (zoneMatch && !line.includes(':')) {
            const zoneName = zoneMatch[1];
            
            // Parantez içindeki status'u ayır
            let status = 'inactive';
            const statusMatch = line.match(/\(([^)]+)\)/);
            if (statusMatch) {
                const statusParts = statusMatch[1].split(',').map(s => s.trim());
                // Son kısım genellikle status (active/inactive)
                if (statusParts.length > 0) {
                    const lastPart = statusParts[statusParts.length - 1].toLowerCase();
                    if (lastPart === 'active' || lastPart === 'inactive') {
                        status = lastPart;
                    } else if (statusParts.some(p => p.toLowerCase() === 'active')) {
                        status = 'active';
                    }
                }
            }
            
            // Önceki zone'u kaydet
            if (currentZone) {
                zones.push(currentZone);
            }
            
            // Yeni zone başlat
            currentZone = {
                name: zoneName,
                status: status,
                target: 'default',
                interfaces: [],
                sources: [],
                services: [],
                ports: [],
                protocols: [],
                forwardPorts: [],
                sourcePorts: [],
                icmpBlocks: [],
                richRules: [],
                masquerade: false,
                totalRules: 0
            };
            continue;
        }
        
        if (!currentZone) continue;
        
        // Zone özelliklerini parse et
        if (line.startsWith('target:')) {
            currentZone.target = line.replace('target:', '').trim();
        } else if (line.startsWith('interfaces:')) {
            const interfaces = line.replace('interfaces:', '').trim();
            currentZone.interfaces = interfaces ? interfaces.split(/\s+/) : [];
        } else if (line.startsWith('sources:')) {
            const sources = line.replace('sources:', '').trim();
            currentZone.sources = sources ? sources.split(/\s+/) : [];
        } else if (line.startsWith('services:')) {
            const services = line.replace('services:', '').trim();
            currentZone.services = services ? services.split(/\s+/) : [];
            currentZone.totalRules += currentZone.services.length;
        } else if (line.startsWith('ports:')) {
            const ports = line.replace('ports:', '').trim();
            // Boş değilse portları ayır
            if (ports) {
                currentZone.ports = ports.split(/\s+/).filter(p => p.length > 0);
                currentZone.totalRules += currentZone.ports.length;
            } else {
                currentZone.ports = [];
            }
        } else if (line.startsWith('protocols:')) {
            const protocols = line.replace('protocols:', '').trim();
            currentZone.protocols = protocols ? protocols.split(/\s+/) : [];
            currentZone.totalRules += currentZone.protocols.length;
        } else if (line.startsWith('forward-ports:')) {
            const forwardPorts = line.replace('forward-ports:', '').trim();
            currentZone.forwardPorts = forwardPorts ? forwardPorts.split(/\s+/) : [];
            currentZone.totalRules += currentZone.forwardPorts.length;
        } else if (line.startsWith('source-ports:')) {
            const sourcePorts = line.replace('source-ports:', '').trim();
            currentZone.sourcePorts = sourcePorts ? sourcePorts.split(/\s+/) : [];
            currentZone.totalRules += currentZone.sourcePorts.length;
        } else if (line.startsWith('icmp-blocks:')) {
            const icmpBlocks = line.replace('icmp-blocks:', '').trim();
            currentZone.icmpBlocks = icmpBlocks ? icmpBlocks.split(/\s+/) : [];
            currentZone.totalRules += currentZone.icmpBlocks.length;
        } else if (line.startsWith('masquerade:')) {
            const masquerade = line.replace('masquerade:', '').trim();
            currentZone.masquerade = masquerade === 'yes';
        } else if (line.startsWith('rich rules:')) {
            // Rich rules çok satırlı olabilir, sonraki satırları oku
            i++;
            while (i < lines.length && lines[i].trim().startsWith('  ')) {
                const richRule = lines[i].trim();
                if (richRule) {
                    currentZone.richRules.push(richRule);
                    currentZone.totalRules++;
                }
                i++;
            }
            i--; // Son satırı tekrar işlemek için
        }
    }
    
    // Son zone'u ekle
    if (currentZone) {
        zones.push(currentZone);
    }
    
    console.log('Parsed Zones:', zones);
    return zones;
}

// ===== GEÇİCİ/KALICI KURAL İŞARETLEME =====
function markTemporaryRules(runtimeZones, permanentZones) {
    // Permanent zone'ları name'e göre map'e çevir
    const permanentMap = {};
    permanentZones.forEach(zone => {
        permanentMap[zone.name] = {
            ports: new Set(zone.ports),
            services: new Set(zone.services),
            protocols: new Set(zone.protocols),
            forwardPorts: new Set(zone.forwardPorts),
            sourcePorts: new Set(zone.sourcePorts),
            icmpBlocks: new Set(zone.icmpBlocks),
            richRules: new Set(zone.richRules)
        };
    });
    
    // Runtime zone'ları işaretle
    runtimeZones.forEach(zone => {
        const permanent = permanentMap[zone.name] || {
            ports: new Set(),
            services: new Set(),
            protocols: new Set(),
            forwardPorts: new Set(),
            sourcePorts: new Set(),
            icmpBlocks: new Set(),
            richRules: new Set()
        };
        
        // Ports işaretle
        zone.ports = zone.ports.map(port => ({
            value: port,
            isTemporary: !permanent.ports.has(port)
        }));
        
        // Services işaretle
        zone.services = zone.services.map(service => ({
            value: service,
            isTemporary: !permanent.services.has(service)
        }));
        
        // Protocols işaretle
        zone.protocols = zone.protocols.map(protocol => ({
            value: protocol,
            isTemporary: !permanent.protocols.has(protocol)
        }));
        
        // Forward Ports işaretle
        zone.forwardPorts = zone.forwardPorts.map(fp => ({
            value: fp,
            isTemporary: !permanent.forwardPorts.has(fp)
        }));
        
        // Source Ports işaretle
        zone.sourcePorts = zone.sourcePorts.map(sp => ({
            value: sp,
            isTemporary: !permanent.sourcePorts.has(sp)
        }));
        
        // ICMP Blocks işaretle
        zone.icmpBlocks = zone.icmpBlocks.map(icmp => ({
            value: icmp,
            isTemporary: !permanent.icmpBlocks.has(icmp)
        }));
        
        // Rich Rules işaretle
        zone.richRules = zone.richRules.map(rr => ({
            value: rr,
            isTemporary: !permanent.richRules.has(rr)
        }));
    });
    
    return runtimeZones;
}

// ===== FIREWALLD KURALLARI GÖRÜNTÜLEME =====
function displayFirewalldRules(zones) {
    const rulesContainer = document.getElementById('firewalldRulesContainer');
    if (!rulesContainer) return;
    
    rulesContainer.innerHTML = '';
    
    zones.forEach((zone, zoneIndex) => {
        const zoneSection = createZoneSection(zone, zoneIndex);
        rulesContainer.appendChild(zoneSection);
    });
}

// ===== ZONE SECTION OLUŞTURMA =====
function createZoneSection(zone, zoneIndex) {
    const section = document.createElement('div');
    section.className = 'zone-section';
    section.style.cssText = 'margin-bottom: 24px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;';
    
    // Zone Header
    const header = document.createElement('div');
    header.className = 'zone-header';
    header.style.cssText = 'background: #f9fafb; padding: 16px 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;';
    header.innerHTML = `
        <div class="zone-title" style="display: flex; align-items: center; gap: 12px;">
            <i class="fas fa-network-wired" style="color: #3b82f6; font-size: 18px;"></i>
            <div>
                <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #111827;">${zone.name} Zone</h3>
                <span style="font-size: 12px; color: #6b7280;">${zone.status === 'active' ? 'Active' : 'Inactive'}</span>
            </div>
        </div>
        <div class="zone-count" style="font-size: 14px; color: #6b7280;">
            ${zone.totalRules} ${zone.totalRules === 1 ? 'rule' : 'rules'}
        </div>
    `;
    
    // Zone Content
    const content = document.createElement('div');
    content.className = 'zone-content';
    content.style.cssText = 'padding: 20px;';
    
    // Services Table
    if (zone.services.length > 0) {
        const servicesTable = createRulesTable('Services', zone.services.map(s => {
            const serviceValue = typeof s === 'string' ? s : s.value;
            const isTemporary = typeof s === 'object' ? s.isTemporary : false;
            return {
                type: 'service',
                value: serviceValue,
                protocol: 'TCP/UDP',
                port: 'N/A',
                isTemporary: isTemporary
            };
        }));
        content.appendChild(servicesTable);
    }
    
    // Ports Table
    if (zone.ports.length > 0) {
        const ports = zone.ports.map(p => {
            const portValue = typeof p === 'string' ? p : p.value;
            const isTemporary = typeof p === 'object' ? p.isTemporary : false;
            const parts = portValue.split('/');
            return {
                type: 'port',
                value: portValue,
                protocol: parts[1] ? parts[1].toUpperCase() : 'TCP',
                port: parts[0],
                isTemporary: isTemporary
            };
        });
        const portsTable = createRulesTable('Ports', ports);
        content.appendChild(portsTable);
    }
    
    // Protocols Table
    if (zone.protocols.length > 0) {
        const protocolsTable = createRulesTable('Protocols', zone.protocols.map(p => {
            const protocolValue = typeof p === 'string' ? p : p.value;
            const isTemporary = typeof p === 'object' ? p.isTemporary : false;
            return {
                type: 'protocol',
                value: protocolValue,
                protocol: protocolValue.toUpperCase(),
                port: 'N/A',
                isTemporary: isTemporary
            };
        }));
        content.appendChild(protocolsTable);
    }
    
    // Forward Ports Table
    if (zone.forwardPorts.length > 0) {
        const forwardPortsTable = createRulesTable('Forward Ports', zone.forwardPorts.map(fp => {
            const fpValue = typeof fp === 'string' ? fp : fp.value;
            const isTemporary = typeof fp === 'object' ? fp.isTemporary : false;
            return {
                type: 'forward-port',
                value: fpValue,
                protocol: 'TCP/UDP',
                port: fpValue,
                isTemporary: isTemporary
            };
        }));
        content.appendChild(forwardPortsTable);
    }
    
    // Source Ports Table
    if (zone.sourcePorts.length > 0) {
        const sourcePortsTable = createRulesTable('Source Ports', zone.sourcePorts.map(sp => {
            const spValue = typeof sp === 'string' ? sp : sp.value;
            const isTemporary = typeof sp === 'object' ? sp.isTemporary : false;
            return {
                type: 'source-port',
                value: spValue,
                protocol: 'TCP/UDP',
                port: spValue,
                isTemporary: isTemporary
            };
        }));
        content.appendChild(sourcePortsTable);
    }
    
    // ICMP Blocks Table
    if (zone.icmpBlocks.length > 0) {
        const icmpBlocksTable = createRulesTable('ICMP Blocks', zone.icmpBlocks.map(icmp => {
            const icmpValue = typeof icmp === 'string' ? icmp : icmp.value;
            const isTemporary = typeof icmp === 'object' ? icmp.isTemporary : false;
            return {
                type: 'icmp-block',
                value: icmpValue,
                protocol: 'ICMP',
                port: 'N/A',
                isTemporary: isTemporary
            };
        }));
        content.appendChild(icmpBlocksTable);
    }
    
    // Rich Rules Table
    if (zone.richRules.length > 0) {
        const richRulesTable = createRulesTable('Rich Rules', zone.richRules.map((rr, idx) => {
            const rrValue = typeof rr === 'string' ? rr : rr.value;
            const isTemporary = typeof rr === 'object' ? rr.isTemporary : false;
            return {
                type: 'rich-rule',
                value: rrValue,
                protocol: 'Any',
                port: 'N/A',
                ruleNumber: idx + 1,
                isTemporary: isTemporary
            };
        }));
        content.appendChild(richRulesTable);
    }
    
    // Zone Info
    const info = document.createElement('div');
    info.className = 'zone-info';
    info.style.cssText = 'margin-top: 16px; padding: 12px; background: #f9fafb; border-radius: 6px; font-size: 13px; color: #6b7280;';
    let infoText = [];
    if (zone.target !== 'default') infoText.push(`Target: ${zone.target}`);
    if (zone.interfaces.length > 0) infoText.push(`Interfaces: ${zone.interfaces.join(', ')}`);
    if (zone.sources.length > 0) infoText.push(`Sources: ${zone.sources.join(', ')}`);
    if (zone.masquerade) infoText.push('Masquerade: enabled');
    info.textContent = infoText.length > 0 ? infoText.join(' | ') : 'No additional configuration';
    
    content.appendChild(info);
    
    section.appendChild(header);
    section.appendChild(content);
    
    return section;
}

// ===== RULES TABLE OLUŞTURMA =====
function createRulesTable(title, rules) {
    const tableContainer = document.createElement('div');
    tableContainer.style.cssText = 'margin-bottom: 20px;';
    
    const tableTitle = document.createElement('h4');
    tableTitle.style.cssText = 'font-size: 14px; font-weight: 600; color: #374151; margin: 0 0 12px 0;';
    tableTitle.textContent = title;
    
    const table = document.createElement('table');
    table.className = 'rules-table';
    
    // Geçici kural var mı kontrol et
    const hasTemporaryRules = rules.some(r => r.isTemporary !== undefined && r.isTemporary);
    table.style.cssText = 'width: 100%; border-collapse: collapse; background: #ffffff;';
    
    // Status kolonu ekle (geçici kural varsa)
    const statusColumn = hasTemporaryRules ? `
        <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #6b7280; width: 100px;">Status</th>
    ` : '';
    
    table.innerHTML = `
        <thead>
            <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb;">
                <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #6b7280; width: 60px;">#</th>
                <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #6b7280;">Value</th>
                <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #6b7280;">Protocol</th>
                <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #6b7280;">Port</th>
                ${statusColumn}
            </tr>
        </thead>
        <tbody>
            ${rules.map((rule, idx) => {
                const isTemporary = rule.isTemporary !== undefined ? rule.isTemporary : false;
                const statusCell = hasTemporaryRules ? `
                    <td style="padding: 12px; font-size: 13px; color: #374151;">
                        ${isTemporary ? 
                            '<span style="display: inline-block; background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 4px; font-weight: 500; font-size: 11px;"><i class="fas fa-clock" style="margin-right: 4px;"></i>Temporary</span>' :
                            '<span style="display: inline-block; background: #d1fae5; color: #065f46; padding: 4px 8px; border-radius: 4px; font-weight: 500; font-size: 11px;"><i class="fas fa-check-circle" style="margin-right: 4px;"></i>Permanent</span>'
                        }
                    </td>
                ` : '';
                
                return `
                <tr style="border-bottom: 1px solid #e5e7eb; ${isTemporary ? 'background: #fffbeb;' : ''}">
                    <td style="padding: 12px; font-size: 13px; color: #6b7280;">
                        <span style="display: inline-block; background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-weight: 600;">${rule.ruleNumber || idx + 1}</span>
                    </td>
                    <td style="padding: 12px; font-size: 13px; color: #111827; font-family: monospace;">${rule.value}</td>
                    <td style="padding: 12px; font-size: 13px; color: #374151;">
                        <span style="display: inline-block; background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-weight: 500;">${rule.protocol}</span>
                    </td>
                    <td style="padding: 12px; font-size: 13px; color: #374151;">${rule.port}</td>
                    ${statusCell}
                </tr>
            `;
            }).join('')}
        </tbody>
    `;
    
    tableContainer.appendChild(tableTitle);
    tableContainer.appendChild(table);
    
    return tableContainer;
}

// ===== EMPTY STATE =====
function showEmptyState() {
    const rulesContainer = document.getElementById('firewalldRulesContainer');
    const rulesEmpty = document.getElementById('firewalldRulesEmpty');
    const rulesLoading = document.getElementById('firewalldRulesLoading');
    
    if (rulesLoading) rulesLoading.style.display = 'none';
    if (rulesContainer) rulesContainer.style.display = 'none';
    if (rulesEmpty) {
        rulesEmpty.style.display = 'flex';
    }
}

// ===== FIREWALLD MEVCUT DEĞİL MESAJI =====
function displayFirewalldUnavailable() {
    const rulesContainer = document.getElementById('firewalldRulesContainer');
    const rulesEmpty = document.getElementById('firewalldRulesEmpty');
    const rulesLoading = document.getElementById('firewalldRulesLoading');
    
    if (rulesLoading) rulesLoading.style.display = 'none';
    if (rulesContainer) rulesContainer.style.display = 'none';
    if (rulesEmpty) {
        rulesEmpty.style.display = 'flex';
        rulesEmpty.innerHTML = `
            <i class="fas fa-shield-alt" style="color: #dc3545;"></i>
            <h3>firewalld is Not Available</h3>
            <p>firewalld is not installed or not available on this system. Please install firewalld to use this feature.</p>
        `;
    }
}

// ===== FIREWALLD AÇMA/KAPAMA =====
function toggleFirewalld() {
    const toggleBtn = document.getElementById('toggleFirewalld');
    const toggleText = document.getElementById('toggleText');
    
    if (!toggleBtn || !toggleText) return;
    
    const originalText = toggleText.textContent;
    
    // Loading durumu
    toggleBtn.disabled = true;
    toggleText.textContent = 'Processing...';
    
    // Mevcut durumu belirle
    const isCurrentlyActive = toggleBtn.classList.contains('active');
    const action = isCurrentlyActive ? 'disable' : 'enable';
    
    fetch('/firewall/firewalld/api/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            action: action
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('firewalld Toggle API Response:', data);
        if (data.success) {
            showNotification(data.message, 'success');
            // Durumu hemen güncelle
            updateStatusAfterToggle(action);
            // Kuralları da yenile
            setTimeout(() => {
                loadFirewalldRules();
                // Status'u da yenile
                loadFirewalldStatus();
            }, 500);
        } else {
            showNotification(data.error || data.message || 'Failed to toggle firewalld', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling firewalld:', error);
        showNotification(`Error: ${error.message}`, 'error');
    })
    .finally(() => {
        toggleBtn.disabled = false;
        toggleText.textContent = originalText;
    });
}

// ===== STATUS GÜNCELLEME =====
function updateStatusAfterToggle(action) {
    const statusIndicator = document.getElementById('firewalldStatusIndicator');
    const toggleBtn = document.getElementById('toggleFirewalld');
    const toggleText = document.getElementById('toggleText');
    
    if (!statusIndicator || !toggleBtn || !toggleText) return;
    
    if (action === 'enable') {
        // Enable yapıldı
        statusIndicator.querySelector('.status-text').textContent = 'Active';
        statusIndicator.querySelector('.status-text').className = 'status-text active';
        statusIndicator.querySelector('.status-dot').className = 'status-dot active';
        toggleText.textContent = 'Disable';
        toggleBtn.className = 'btn-toggle active';
    } else {
        // Disable yapıldı
        statusIndicator.querySelector('.status-text').textContent = 'Inactive';
        statusIndicator.querySelector('.status-text').className = 'status-text inactive';
        statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
        toggleText.textContent = 'Enable';
        toggleBtn.className = 'btn-toggle';
    }
}

// ===== SESSIZ STATUS KONTROLÜ =====
function checkFirewalldStatus() {
    fetch('/firewall/firewalld/api/status/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.available) {
                const statusIndicator = document.getElementById('firewalldStatusIndicator');
                const toggleBtn = document.getElementById('toggleFirewalld');
                const toggleText = document.getElementById('toggleText');
                
                if (!statusIndicator || !toggleBtn || !toggleText) return;
                
                if (data.status === 'active') {
                    // Eğer status değişmişse güncelle
                    if (!statusIndicator.querySelector('.status-dot').classList.contains('active')) {
                        statusIndicator.querySelector('.status-text').textContent = 'Active';
                        statusIndicator.querySelector('.status-text').className = 'status-text active';
                        statusIndicator.querySelector('.status-dot').className = 'status-dot active';
                        toggleText.textContent = 'Disable';
                        toggleBtn.className = 'btn-toggle active';
                        
                        // Status değiştiğinde kuralları da yenile
                        loadFirewalldRules();
                    }
                } else {
                    // Eğer status değişmişse güncelle
                    if (!statusIndicator.querySelector('.status-dot').classList.contains('inactive')) {
                        statusIndicator.querySelector('.status-text').textContent = 'Inactive';
                        statusIndicator.querySelector('.status-text').className = 'status-text inactive';
                        statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
                        toggleText.textContent = 'Enable';
                        toggleBtn.className = 'btn-toggle';
                        
                        // Status değiştiğinde kuralları da yenile
                        loadFirewalldRules();
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error checking firewalld status:', error);
        });
}

// ===== CSRF TOKEN =====
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// ===== NOTIFICATION SISTEMI =====
function showNotification(message, type = 'info') {
    // Mevcut notification'ları temizle
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Yeni notification oluştur
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Notification stilleri
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'info': '#007bff'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 12px;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    
    // Notification içeriği stilleri
    const content = notification.querySelector('.notification-content');
    content.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
    `;
    
    // Kapatma butonu stilleri
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: background 0.2s ease;
    `;
    
    closeBtn.addEventListener('mouseenter', function() {
        this.style.background = 'rgba(255, 255, 255, 0.2)';
    });
    
    closeBtn.addEventListener('mouseleave', function() {
        this.style.background = 'none';
    });
    
    // Body'ye ekle
    document.body.appendChild(notification);
    
    // 5 saniye sonra otomatik kaldır
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// ===== CSS ANIMATIONS =====
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

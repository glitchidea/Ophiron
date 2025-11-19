// ===== IPTABLES FIREWALL JAVASCRIPT - MODULAR COMPONENTS =====

// ===== COMPONENT INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    // Initialize iptables components
    initializeIptablesComponents();
    
    // Load initial data
    loadIptablesStatus();
    loadIptablesRules();
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup auto-refresh
    setupAutoRefresh();
});

// ===== COMPONENT INITIALIZATION =====
function initializeIptablesComponents() {
    console.log('Initializing iptables components...');
    
    // Initialize status indicator
    initializeStatusIndicator();
    
    // Initialize rules table
    initializeRulesTable();
    
    // Initialize loading states
    initializeLoadingStates();
}

// ===== STATUS INDICATOR COMPONENT =====
function initializeStatusIndicator() {
    const statusIndicator = document.getElementById('iptablesStatusIndicator');
    if (statusIndicator) {
        statusIndicator.querySelector('.status-text').textContent = 'Checking...';
        statusIndicator.querySelector('.status-dot').className = 'status-dot';
    }
}

// ===== RULES TABLE COMPONENT =====
function initializeRulesTable() {
    const rulesTable = document.getElementById('iptablesRulesTable');
    const rulesLoading = document.getElementById('iptablesRulesLoading');
    const rulesEmpty = document.getElementById('iptablesRulesEmpty');
    
    if (rulesTable) {
        rulesTable.style.display = 'none';
    }
    if (rulesLoading) {
        rulesLoading.style.display = 'flex';
    }
    if (rulesEmpty) {
        rulesEmpty.style.display = 'none';
    }
}

// ===== LOADING STATES COMPONENT =====
function initializeLoadingStates() {
    const rulesCount = document.getElementById('rulesCount');
    if (rulesCount) {
        rulesCount.textContent = '(0)';
    }
}

// ===== EVENT LISTENERS SETUP =====
function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshIptables');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshAllData();
        });
    }
    
    // Page focus events
    window.addEventListener('focus', function() {
        loadIptablesStatus();
    });
    
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            loadIptablesStatus();
        }
    });
}

// ===== AUTO REFRESH COMPONENT =====
function setupAutoRefresh() {
    // Auto-refresh every 5 seconds
    setInterval(function() {
        checkIptablesStatus();
    }, 5000);
}

// ===== DATA LOADING COMPONENTS =====

// ===== IPTABLES STATUS LOADING =====
function loadIptablesStatus() {
    const statusIndicator = document.getElementById('iptablesStatusIndicator');
    
    if (!statusIndicator) return;
    
    // Loading state
    statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.checking || 'Checking...';
    statusIndicator.querySelector('.status-dot').className = 'status-dot';
    
    fetch('/firewall/iptables/api/status/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateStatusIndicator(data);
        })
        .catch(error => {
            console.error('Error loading iptables status:', error);
            statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.error || 'Error';
            statusIndicator.querySelector('.status-text').className = 'status-text inactive';
            statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
        });
}

// ===== IPTABLES RULES LOADING =====
function loadIptablesRules() {
    const rulesLoading = document.getElementById('iptablesRulesLoading');
    const rulesContainer = document.getElementById('iptablesRulesContainer');
    const rulesEmpty = document.getElementById('iptablesRulesEmpty');
    const rulesCount = document.getElementById('rulesCount');
    
    if (!rulesLoading || !rulesContainer || !rulesEmpty || !rulesCount) return;
    
    // Show loading state
    rulesLoading.style.display = 'flex';
    rulesContainer.style.display = 'none';
    rulesEmpty.style.display = 'none';
    rulesCount.textContent = '(0)';
    
    // Update loading text
    const loadingText = rulesLoading.querySelector('span');
    if (loadingText) {
        loadingText.textContent = window.jsTranslations.loading_rules || 'Loading rules...';
    }
    
    fetch('/firewall/iptables/api/rules/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            rulesLoading.style.display = 'none';
            
            if (data.success && data.rules) {
                console.log('iptables API Response:', data);
                const rules = parseIptablesRules(data.rules);
                
                if (rules.length > 0) {
                    displayIptablesRules(rules);
                    rulesContainer.style.display = 'block';
                    rulesCount.textContent = `(${rules.length})`;
                } else {
                    showEmptyState();
                }
            } else {
                showEmptyState();
            }
        })
        .catch(error => {
            console.error('Error loading iptables rules:', error);
            rulesLoading.style.display = 'none';
            showEmptyState();
        });
}

// ===== RULES PARSING COMPONENT =====
function parseIptablesRules(rulesOutput) {
    const lines = rulesOutput.split('\n');
    const rules = [];
    let ruleNumber = 1;
    let currentTable = 'filter'; // Default table
    let currentChain = 'INPUT'; // Default chain
    
    console.log('iptables Rules Output:', rulesOutput);
    
    for (let line of lines) {
        line = line.trim();
        
        // Skip empty lines
        if (!line) continue;
        
        // Detect table changes
        if (line.startsWith('=== ') && line.endsWith(' TABLE ===')) {
            const tableMatch = line.match(/=== (\w+) TABLE ===/);
            if (tableMatch) {
                currentTable = tableMatch[1].toLowerCase();
                console.log('Switched to table:', currentTable);
                continue;
            }
        }
        
        // Detect chain headers
        if (line.startsWith('Chain ')) {
            console.log('Found chain:', line);
            // Extract chain name from "Chain INPUT (policy ACCEPT)"
            const chainMatch = line.match(/Chain (\w+)/);
            if (chainMatch) {
                currentChain = chainMatch[1];
                console.log('Switched to chain:', currentChain);
            }
            continue;
        }
        
        // Skip headers
        if (line.includes('target') && line.includes('prot') && line.includes('source')) {
            continue;
        }
        
        // Skip packet counters line
        if (line.includes('pkts') && line.includes('bytes')) {
            continue;
        }
        
        // Skip policy lines (like "target     prot opt source               destination")
        if (line.includes('target') && line.includes('prot') && line.includes('opt')) {
            continue;
        }
        
        // Parse iptables rule format
        const rule = parseIptablesRule(line, currentTable, currentChain);
        if (rule) {
            rule.ruleNumber = ruleNumber++;
            rules.push(rule);
            console.log('Added rule:', rule);
        }
    }
    
    console.log('Parsed Rules:', rules);
    return rules;
}

// ===== SINGLE RULE PARSING =====
function parseIptablesRule(line, table = 'filter', chain = 'INPUT') {
    // Skip lines that are not actual rules
    if (line.startsWith('Chain ') || line.includes('target') || line.includes('pkts') || line.includes('bytes')) {
        return null;
    }
    
    // Split by multiple spaces to handle iptables output format
    const parts = line.split(/\s+/).filter(part => part.length > 0);
    
    if (parts.length < 2) return null;
    
    // Extract rule number if present (first element might be a number)
    let ruleNumber = null;
    let startIndex = 0;
    
    if (parts[0].match(/^\d+$/)) {
        ruleNumber = parseInt(parts[0]);
        startIndex = 1;
    }
    
    if (parts.length < startIndex + 2) return null;
    
    const rule = {
        table: table,
        chain: chain,  // Chain'i parametre olarak al
        target: parts[startIndex + 1] || 'UNKNOWN',
        protocol: 'any',
        source: 'anywhere',
        destination: 'anywhere',
        port: 'any',
        interface: 'any',
        match: '',
        options: '',
        ruleNumber: ruleNumber
    };
    
    // Parse the rule line more comprehensively
    let i = startIndex + 2; // Start after chain and target
    
    while (i < parts.length) {
        const part = parts[i];
        
        // Protocol
        if (part === 'tcp' || part === 'udp' || part === 'icmp' || part === 'all') {
            rule.protocol = part;
        }
        // Source IP
        else if (part === '0.0.0.0/0' || part === 'anywhere') {
            rule.source = 'anywhere';
        }
        else if (part.match(/^\d+\.\d+\.\d+\.\d+/) || part.match(/^\d+\.\d+\.\d+\.\d+\/\d+/)) {
            rule.source = part;
        }
        // Destination IP
        else if (part === '0.0.0.0/0' || part === 'anywhere') {
            rule.destination = 'anywhere';
        }
        else if (part.match(/^\d+\.\d+\.\d+\.\d+/) || part.match(/^\d+\.\d+\.\d+\.\d+\/\d+/)) {
            rule.destination = part;
        }
        // Port information
        else if (part.includes('dpt:') || part.includes('spt:')) {
            const portMatch = part.match(/(dpt|spt):(\w+)/);
            if (portMatch) {
                rule.port = portMatch[2];
            }
        }
        // Interface information
        else if (part.includes('in:') || part.includes('out:')) {
            const ifaceMatch = part.match(/(in|out):(\w+)/);
            if (ifaceMatch) {
                rule.interface = ifaceMatch[2];
            }
        }
        // Match modules
        else if (part.startsWith('state') || part.startsWith('conntrack') || 
                 part.startsWith('multiport') || part.startsWith('limit') ||
                 part.startsWith('recent') || part.startsWith('mac') ||
                 part.startsWith('owner') || part.startsWith('time')) {
            rule.match = part;
        }
        // Options and parameters
        else if (part.startsWith('--') || part.includes('=') || part.includes(':')) {
            rule.options += (rule.options ? ' ' : '') + part;
        }
        
        i++;
    }
    
    // Clean up options
    rule.options = rule.options.trim();
    
    // Only return valid rules
    if (rule.chain === 'UNKNOWN' || rule.target === 'UNKNOWN') {
        return null;
    }
    
    console.log('Parsed rule:', rule);
    return rule;
}

// ===== RULES DISPLAY COMPONENT =====
function displayIptablesRules(rules) {
    const rulesContainer = document.getElementById('iptablesRulesContainer');
    if (!rulesContainer) return;
    
    // Group rules by chain
    const rulesByChain = groupRulesByChain(rules);
    
    rulesContainer.innerHTML = '';
    
    // Create sections for each chain
    Object.keys(rulesByChain).forEach(chainName => {
        const chainRules = rulesByChain[chainName];
        const chainSection = createChainSection(chainName, chainRules);
        rulesContainer.appendChild(chainSection);
    });
}

// ===== GROUP RULES BY CHAIN =====
function groupRulesByChain(rules) {
    const grouped = {};
    
    rules.forEach(rule => {
        const chainKey = `${rule.table}-${rule.chain}`;
        if (!grouped[chainKey]) {
            grouped[chainKey] = {
                table: rule.table,
                chain: rule.chain,
                rules: []
            };
        }
        grouped[chainKey].rules.push(rule);
    });
    
    return grouped;
}

// ===== CREATE CHAIN SECTION =====
function createChainSection(chainKey, chainData) {
    const section = document.createElement('div');
    section.className = 'chain-section';
    
    const header = document.createElement('div');
    header.className = 'chain-header';
    header.innerHTML = `
        <div class="chain-title">
            <i class="fas fa-${getChainIcon(chainData.chain)}"></i>
            ${chainData.chain} Chain (${chainData.table})
        </div>
        <div class="chain-count">${chainData.rules.length} ${window.jsTranslations.rules || 'rules'}</div>
    `;
    
    const table = document.createElement('table');
    table.className = 'chain-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th class="col-number">#</th>
                <th class="col-target">${window.jsTranslations.target || 'Target'}</th>
                <th class="col-protocol">${window.jsTranslations.protocol || 'Protocol'}</th>
                <th class="col-source">${window.jsTranslations.source || 'Source'}</th>
                <th class="col-destination">${window.jsTranslations.destination || 'Destination'}</th>
                <th class="col-port">${window.jsTranslations.port || 'Port'}</th>
                <th class="col-interface">Interface</th>
                <th class="col-match">Match</th>
                <th class="col-options">${window.jsTranslations.options || 'Options'}</th>
                <th class="col-actions">Actions</th>
            </tr>
        </thead>
        <tbody>
            ${chainData.rules.map(rule => `
                <tr>
                    <td class="col-number">
                        <span class="rule-number-badge">${rule.ruleNumber}</span>
                    </td>
                    <td class="col-target">
                        <span class="rule-target ${rule.target.toLowerCase()}">
                            <i class="fas fa-${getTargetIcon(rule.target)}"></i>
                            ${rule.target}
                        </span>
                    </td>
                    <td class="col-protocol">
                        <span class="rule-protocol">${rule.protocol}</span>
                    </td>
                    <td class="col-source">
                        <span class="rule-address">${rule.source}</span>
                    </td>
                    <td class="col-destination">
                        <span class="rule-address">${rule.destination}</span>
                    </td>
                    <td class="col-port">
                        <span class="rule-port">${rule.port}</span>
                    </td>
                    <td class="col-interface">
                        <span class="rule-interface">${rule.interface}</span>
                    </td>
                    <td class="col-match">
                        <span class="rule-match">${rule.match}</span>
                    </td>
                    <td class="col-options">
                        <span class="rule-options">${rule.options}</span>
                    </td>
                    <td class="col-actions">
                        <div class="rule-actions">
                            <button class="btn-delete-rule" onclick="deleteIptablesRule('${rule.table}', '${rule.chain}', ${rule.ruleNumber}, ${JSON.stringify(rule).replace(/"/g, '&quot;')})" title="${window.jsTranslations.delete_rule || 'Delete Rule'}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    section.appendChild(header);
    section.appendChild(table);
    
    return section;
}

// ===== HELPER FUNCTIONS =====
function getTableIcon(table) {
    const tableIcons = {
        'filter': 'shield-alt',
        'nat': 'exchange-alt',
        'mangle': 'cogs',
        'raw': 'code',
        'security': 'lock'
    };
    return tableIcons[table.toLowerCase()] || 'table';
}

function getChainIcon(chain) {
    const chainIcons = {
        'INPUT': 'arrow-down',
        'FORWARD': 'arrow-right',
        'OUTPUT': 'arrow-up',
        'PREROUTING': 'arrow-right',
        'POSTROUTING': 'arrow-right'
    };
    return chainIcons[chain.toUpperCase()] || 'question';
}

function getTargetIcon(target) {
    const targetIcons = {
        'ACCEPT': 'check',
        'DROP': 'times',
        'REJECT': 'ban',
        'RETURN': 'undo',
        'LOG': 'file-alt',
        'DNAT': 'exchange-alt',
        'SNAT': 'exchange-alt',
        'MASQUERADE': 'mask',
        'REDIRECT': 'external-link-alt',
        'MARK': 'tag',
        'CONNMARK': 'bookmark',
        'TTL': 'clock',
        'TCPMSS': 'ruler',
        'CLASSIFY': 'sort',
        'CONNSECMARK': 'shield',
        'TOS': 'flag',
        'ECN': 'exclamation',
        'DSCP': 'layer-group',
        'NOTRACK': 'eye-slash',
        'SECMARK': 'shield-alt',
        'AUDIT': 'clipboard-check',
        'CHECKSUM': 'calculator',
        'CLUSTERIP': 'network-wired',
        'IDLETIMER': 'hourglass-half',
        'LED': 'lightbulb',
        'NFLOG': 'file-alt',
        'NFQUEUE': 'list',
        'RATEEST': 'chart-line',
        'SAME': 'equals',
        'TCPOPTSTRIP': 'cut'
    };
    return targetIcons[target.toUpperCase()] || 'question';
}

// ===== STATUS UPDATE COMPONENT =====
function updateStatusIndicator(data) {
    const statusIndicator = document.getElementById('iptablesStatusIndicator');
    if (!statusIndicator) return;
    
    if (data.available) {
        if (data.status === 'active') {
            statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.enabled || 'Active';
            statusIndicator.querySelector('.status-text').className = 'status-text active';
            statusIndicator.querySelector('.status-dot').className = 'status-dot active';
        } else {
            statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.disabled || 'Inactive';
            statusIndicator.querySelector('.status-text').className = 'status-text inactive';
            statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
        }
    } else {
        statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.not_available || 'Not Available';
        statusIndicator.querySelector('.status-text').className = 'status-text inactive';
        statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
    }
}

// ===== EMPTY STATE COMPONENT =====
function showEmptyState() {
    const rulesContainer = document.getElementById('iptablesRulesContainer');
    const rulesEmpty = document.getElementById('iptablesRulesEmpty');
    const rulesCount = document.getElementById('rulesCount');
    
    if (rulesContainer) rulesContainer.style.display = 'none';
    if (rulesEmpty) rulesEmpty.style.display = 'flex';
    if (rulesCount) rulesCount.textContent = '(0)';
}

// ===== REFRESH COMPONENT =====
function refreshAllData() {
    loadIptablesStatus();
    loadIptablesRules();
}

// ===== STATUS CHECK COMPONENT =====
function checkIptablesStatus() {
    fetch('/firewall/iptables/api/status/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateStatusIndicator(data);
        })
        .catch(error => {
            console.error('Error checking iptables status:', error);
        });
}

// ===== NOTIFICATION COMPONENT =====
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
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
    
    // Notification styles
    const colors = {
        'success': '#059669',
        'error': '#dc2626',
        'info': '#3b82f6'
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
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// ===== TEST FUNCTION =====
function testIptablesRules() {
    console.log('Testing iptables rules loading...');
    fetch('/firewall/iptables/api/rules/')
        .then(response => response.json())
        .then(data => {
            console.log('Raw iptables API Response:', data);
            if (data.success && data.rules) {
                console.log('Raw iptables Rules Output:');
                console.log(data.rules);
                const rules = parseIptablesRules(data.rules);
                console.log('Parsed Rules:', rules);
                console.log('Total rules found:', rules.length);
            }
        })
        .catch(error => {
            console.error('Test error:', error);
        });
}

// Make test function global
window.testIptablesRules = testIptablesRules;

// ===== RULE MANAGEMENT FUNCTIONS =====

// Delete iptables rule with modal confirmation
function deleteIptablesRule(table, chain, ruleNumber, ruleData = null) {
    // Modal'ı aç ve bilgileri doldur
    const modal = new bootstrap.Modal(document.getElementById('iptablesDeleteModal'));
    
    // Modal içeriğini doldur
    document.getElementById('deleteTableName').textContent = table;
    document.getElementById('deleteChainName').textContent = chain;
    document.getElementById('deleteRuleNumber').textContent = ruleNumber;
    
    if (ruleData) {
        document.getElementById('deleteRuleTarget').textContent = ruleData.target || '-';
        document.getElementById('deleteRuleProtocol').textContent = ruleData.protocol || '-';
        document.getElementById('deleteRuleSource').textContent = ruleData.source || '-';
        document.getElementById('deleteRuleDestination').textContent = ruleData.destination || '-';
    } else {
        document.getElementById('deleteRuleTarget').textContent = '-';
        document.getElementById('deleteRuleProtocol').textContent = '-';
        document.getElementById('deleteRuleSource').textContent = '-';
        document.getElementById('deleteRuleDestination').textContent = '-';
    }
    
    // Checkbox'ı sıfırla
    document.getElementById('confirmDelete').checked = false;
    document.getElementById('confirmDeleteBtn').disabled = true;
    
    // Checkbox event listener
    document.getElementById('confirmDelete').addEventListener('change', function() {
        document.getElementById('confirmDeleteBtn').disabled = !this.checked;
    });
    
    // Delete button event listener
    document.getElementById('confirmDeleteBtn').onclick = function() {
        if (document.getElementById('confirmDelete').checked) {
            performDeleteRule(table, chain, ruleNumber);
            modal.hide();
        }
    };
    
    modal.show();
}

// Actual delete function
function performDeleteRule(table, chain, ruleNumber) {
    showNotification(`${window.jsTranslations.deleting_rule || 'Deleting rule'} ${ruleNumber} (${table}.${chain})...`, 'info');
    
    fetch('/firewall/iptables/api/delete-rule/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            table: table,
            chain: chain,
            rule_number: ruleNumber
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Delete rule response:', data);
        if (data.success) {
            showNotification(`✅ ${data.message}`, 'success');
            // Refresh rules after successful deletion
            setTimeout(() => {
                loadIptablesRules();
            }, 1000);
        } else {
            // Daha detaylı hata mesajı göster
            const errorMessage = data.message || data.error || (window.jsTranslations.error_deleting_rule || 'Error deleting rule');
            showNotification(`❌ ${errorMessage}`, 'error');
            console.error('Delete rule error:', data);
        }
    })
    .catch(error => {
        console.error('Error deleting iptables rule:', error);
        showNotification(`❌ ${window.jsTranslations.connection_error || 'Connection error'}: ${error.message}`, 'error');
    });
}


// Delete rule by specification
function deleteIptablesRuleBySpec(table, chain, ruleSpec) {
    if (!confirm(`Are you sure you want to delete this rule from ${table}.${chain}?`)) {
        return;
    }
    
    showNotification(`Deleting rule from ${table}.${chain}...`, 'info');
    
    fetch('/firewall/iptables/api/delete-rule-by-spec/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            table: table,
            chain: chain,
            rule_spec: ruleSpec
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // Refresh rules after successful deletion
            setTimeout(() => {
                loadIptablesRules();
            }, 1000);
        } else {
            showNotification(data.error || data.message || 'Failed to delete rule', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting iptables rule:', error);
        showNotification(`Error: ${error.message}`, 'error');
    });
}

// Flush chain
function flushIptablesChain(table, chain) {
    if (!confirm(`Are you sure you want to flush all rules from ${table}.${chain}? This action cannot be undone!`)) {
        return;
    }
    
    showNotification(`Flushing chain ${chain} in table ${table}...`, 'info');
    
    fetch('/firewall/iptables/api/flush-chain/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            table: table,
            chain: chain
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // Refresh rules after successful flush
            setTimeout(() => {
                loadIptablesRules();
            }, 1000);
        } else {
            showNotification(data.error || data.message || 'Failed to flush chain', 'error');
        }
    })
    .catch(error => {
        console.error('Error flushing iptables chain:', error);
        showNotification(`Error: ${error.message}`, 'error');
    });
}

// CSRF Token function
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Make functions global
window.deleteIptablesRule = deleteIptablesRule;
window.deleteIptablesRuleBySpec = deleteIptablesRuleBySpec;
window.flushIptablesChain = flushIptablesChain;

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
    
    /* Rule Actions Styles */
    .rule-actions {
        display: flex;
        gap: 4px;
        align-items: center;
    }
    
    .btn-delete-rule {
        background: none;
        border: none;
        padding: 6px 8px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 12px;
        color: #dc2626;
        background: #fef2f2;
    }
    
    .btn-delete-rule:hover {
        background: #dc2626;
        color: white;
    }
    
    .col-actions {
        width: 8%;
        min-width: 80px;
        text-align: center;
    }
`;
document.head.appendChild(style);

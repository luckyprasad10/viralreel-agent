let currentTab = 'ready';
let autoRefreshTimer = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchQueue(currentTab);
    fetchLogs();
    fetchProfile();
    fetchDecisions();
    fetchChatHistory();

    // Auto-refresh stats & logs
    autoRefreshTimer = setInterval(() => {
        fetchStats();
        fetchLogs();
        fetchProfile();
        fetchDecisions();
    }, 4000);

    // Autonomous Mode switch listener
    const autoToggle = document.getElementById('autoModeToggle');
    if (autoToggle) {
        autoToggle.addEventListener('change', async (e) => {
            try {
                const res = await fetch('/api/actions/toggle-autonomous', { method: 'POST' });
                const data = await res.json();
                showToast(data.autonomous_mode ? 'Autonomous Mode Activated! ⚡' : 'Switched to Manual Approval Mode');
            } catch (err) {
                showToast('Failed to toggle autonomous mode', 'error');
            }
        });
    }
});

// Switch Filter Tabs
function switchTab(tab, el) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    if (el) el.classList.add('active');
    fetchQueue(tab);
}

// Fetch Dashboard Stats
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        document.getElementById('statDiscovered').textContent = data.total_discovered || 0;
        document.getElementById('statReady').textContent = data.ready_count || 0;
        document.getElementById('statPosted').textContent = data.posted_count || 0;
        document.getElementById('statPostsToday').textContent = data.posts_today || 0;
        document.getElementById('statMaxDaily').textContent = data.max_daily || 3;
        document.getElementById('statViews').textContent = (data.total_insta_views || 0).toLocaleString();

        const accountPill = document.getElementById('accountPill');
        const accountText = document.getElementById('accountStatusText');
        if (data.insta_connected) {
            accountPill.className = 'account-pill glass connected';
            accountText.textContent = 'Instagram Active';
        } else {
            accountPill.className = 'account-pill glass disconnected';
            accountText.textContent = 'Connect Instagram';
        }
    } catch (e) {
        console.error('Stats error:', e);
    }
}

// Fetch Content Queue
async function fetchQueue(status = 'ready') {
    const container = document.getElementById('videoCardsList');
    try {
        const url = status === 'all' ? '/api/queue?limit=40' : `/api/queue?status=${status}&limit=40`;
        const res = await fetch(url);
        const data = await res.json();
        const videos = data.videos || [];

        if (videos.length === 0) {
            container.innerHTML = `
                <div class="glass" style="padding: 40px; text-align: center; border-radius: var(--radius-lg); color: var(--text-muted);">
                    <div style="font-size: 32px; margin-bottom: 8px;">📭</div>
                    <div>No videos found under <strong>${status}</strong>.</div>
                    <div style="margin-top: 10px;">Click <strong>"⚡ Discover Viral Videos"</strong> above to hunt fresh trending TikToks.</div>
                </div>
            `;
            return;
        }

        container.innerHTML = videos.map(v => renderVideoCard(v)).join('');
    } catch (e) {
        console.error('Queue fetch error:', e);
        container.innerHTML = `<div style="color: var(--accent-red); padding: 20px;">Failed to load queue.</div>`;
    }
}

// Render individual video card
function renderVideoCard(v) {
    const regionFlag = v.region === 'US' ? '🇺🇸' : v.region === 'GB' ? '🇬🇧' : v.region === 'AU' ? '🇦🇺' : '🌐';
    const hasProcessed = v.processed_video_path && v.status !== 'discovered';
    const videoUrl = hasProcessed ? `/media/processed/${v.tiktok_id}_insta.mp4` : null;

    return `
        <div class="video-card glass">
            <div class="video-thumb-container">
                <img class="video-thumb" src="${v.cover_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=300'}" alt="Cover" loading="lazy">
                <span class="badge-overlay">${regionFlag} ${v.region || 'US'}</span>
                <span class="badge-virality">🔥 ${v.virality_score || 0} pts</span>
            </div>

            <div class="video-info">
                <div>
                    <div class="video-header">
                        <div>
                            <h3 class="video-title">${escapeHtml(v.original_title || 'Untitled Viral Clip')}</h3>
                            <span class="video-author">@${v.author || 'creator'} • TikTok</span>
                        </div>
                        <span class="status-badge status-${v.status}">${v.status}</span>
                    </div>

                    <div class="metrics-row">
                        <span class="metric-item">👁️ ${(v.views || 0).toLocaleString()}</span>
                        <span class="metric-item">❤️ ${(v.likes || 0).toLocaleString()}</span>
                        <span class="metric-item">💬 ${(v.comments || 0).toLocaleString()}</span>
                        <span class="metric-item">↗️ ${(v.shares || 0).toLocaleString()}</span>
                    </div>

                    ${v.ai_caption ? `
                        <div class="caption-preview-box">
                            <strong>AI Hook & Caption:</strong><br>
                            ${escapeHtml(v.ai_caption)}
                        </div>
                    ` : ''}
                </div>

                <div class="video-actions">
                    ${v.status === 'ready' || v.status === 'discovered' ? `
                        <button class="btn btn-primary btn-sm" onclick="approveAndPost(${v.id})">
                            🚀 Post to Instagram
                        </button>
                    ` : ''}

                    ${v.status === 'discovered' ? `
                        <button class="btn btn-secondary btn-sm" onclick="prepareVideo(${v.id})">
                            ⚡ Download & Process (9:16)
                        </button>
                    ` : ''}

                    ${hasProcessed ? `
                        <button class="btn btn-secondary btn-sm" onclick="openPreviewModal('${videoUrl}')">
                            👁️ Preview Reel
                        </button>
                    ` : ''}

                    ${v.status === 'posted' && v.insta_code ? `
                        <a href="https://www.instagram.com/reel/${v.insta_code}/" target="_blank" class="btn btn-success btn-sm" style="text-decoration: none;">
                            📸 View on Instagram
                        </a>
                    ` : ''}

                    <a href="${v.tiktok_url}" target="_blank" class="btn btn-secondary btn-sm" style="text-decoration: none; opacity: 0.8;">
                        🔗 Original TikTok
                    </a>
                </div>
            </div>
        </div>
    `;
}

// Fetch Activity Logs
async function fetchLogs() {
    try {
        const res = await fetch('/api/logs?limit=40');
        const data = await res.json();
        const logs = data.logs || [];
        const container = document.getElementById('logsContainer');

        if (logs.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); font-size: 12px;">No activity logged yet.</div>';
            return;
        }

        container.innerHTML = logs.map(l => `
            <div class="log-entry ${l.level}">
                <div class="log-meta">
                    <span class="log-module">[${l.module}]</span>
                    <span>${formatTime(l.created_at)}</span>
                </div>
                <div>${escapeHtml(l.message)}</div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Logs fetch error:', e);
    }
}

// User Actions
async function triggerDiscovery() {
    showToast('Hunting viral comedy & entertainment TikToks... ⚡');
    try {
        const res = await fetch('/api/actions/discover', { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
        setTimeout(() => {
            fetchStats();
            fetchQueue(currentTab);
        }, 3000);
    } catch (e) {
        showToast('Error triggering discovery', 'error');
    }
}

async function triggerPostNext() {
    showToast('Publishing next ready Reel to Instagram... 🚀');
    try {
        const res = await fetch('/api/actions/post-next', { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
        setTimeout(() => {
            fetchStats();
            fetchQueue(currentTab);
        }, 4000);
    } catch (e) {
        showToast('Error publishing reel', 'error');
    }
}

async function approveAndPost(videoId) {
    showToast(`Queueing video ${videoId} for Instagram publishing... 🚀`);
    try {
        const res = await fetch(`/api/actions/approve-post/${videoId}`, { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
        setTimeout(() => {
            fetchStats();
            fetchQueue(currentTab);
        }, 3000);
    } catch (e) {
        showToast('Error submitting post', 'error');
    }
}

async function prepareVideo(videoId) {
    showToast(`Processing video ${videoId} (FFmpeg 9:16 + anti-duplicate)... ⚡`);
    try {
        const res = await fetch(`/api/actions/prepare/${videoId}`, { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
        setTimeout(() => {
            fetchStats();
            fetchQueue(currentTab);
        }, 4000);
    } catch (e) {
        showToast('Error preparing video', 'error');
    }
}

// Modal Handlers
function openLoginModal() {
    document.getElementById('loginModal').style.display = 'flex';
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
}

function openPreviewModal(videoUrl) {
    if (!videoUrl) return;
    const player = document.getElementById('previewVideoPlayer');
    player.src = videoUrl;
    document.getElementById('previewModal').style.display = 'flex';
    player.play().catch(() => {});
}

function closePreviewModal() {
    const player = document.getElementById('previewVideoPlayer');
    player.pause();
    player.src = '';
    document.getElementById('previewModal').style.display = 'none';
}

async function handleInstaLogin(e) {
    e.preventDefault();
    const user = document.getElementById('instaUser').value;
    const pass = document.getElementById('instaPass').value;
    const code = document.getElementById('insta2fa').value;

    showToast('Authenticating with Instagram...');
    try {
        const res = await fetch('/api/instagram/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass, verification_code: code || null })
        });
        const data = await res.json();

        if (data.success) {
            showToast('Instagram connected successfully! 🎉');
            closeLoginModal();
            fetchStats();
        } else if (data.status === '2fa_required') {
            document.getElementById('twoFactorGroup').style.display = 'block';
            showToast('2FA required: Enter your security code above', 'warn');
        } else {
            showToast(data.message || 'Login failed', 'error');
        }
    } catch (err) {
        showToast('Login request error', 'error');
    }
}

// Toast Helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast glass';
    const icon = type === 'error' ? '❌' : type === 'warn' ? '⚠️' : '⚡';
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = '0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function formatTime(isoStr) {
    if (!isoStr) return '';
    try {
        const d = new Date(isoStr);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
        return isoStr;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[m]);
}

// --- 🧠 AI Agent & Instagram Profile Functions ---

async function fetchProfile() {
    try {
        const res = await fetch('/api/instagram/profile');
        const data = await res.json();

        if (data.connected) {
            document.getElementById('profileFullName').textContent = data.full_name || data.username;
            document.getElementById('profileUsername').textContent = '@' + data.username;
            document.getElementById('profileFollowers').textContent = (data.followers || 0).toLocaleString();
            document.getElementById('profileFollowing').textContent = (data.following || 0).toLocaleString();
            document.getElementById('profilePostsCount').textContent = (data.media_count || 0).toLocaleString();
            if (data.biography) {
                document.getElementById('profileBio').textContent = data.biography;
            }
            if (data.profile_pic_url) {
                document.getElementById('profileAvatar').src = data.profile_pic_url;
            }
        }
    } catch (e) {
        console.error('Profile fetch error:', e);
    }
}

async function fetchDecisions() {
    try {
        const res = await fetch('/api/agent/decisions?limit=15');
        const data = await res.json();
        const decisions = data.decisions || [];
        const container = document.getElementById('decisionsContainer');

        if (decisions.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); font-size: 12px;">AI Director is initializing strategy...</div>';
            return;
        }

        container.innerHTML = decisions.map(d => `
            <div class="decision-card">
                <div class="decision-header">
                    <span>⚡ ${escapeHtml(d.action_type || 'TACTIC')}</span>
                    <span style="font-size: 10px; color: var(--text-muted);">${formatTime(d.created_at)}</span>
                </div>
                <div style="color: #e2e8f0; margin-bottom: 4px;">${escapeHtml(d.reasoning || '')}</div>
                ${d.impact ? `<div style="color: var(--accent-green); font-size: 11px;">✓ ${escapeHtml(d.impact)}</div>` : ''}
            </div>
        `).join('');
    } catch (e) {
        console.error('Decisions fetch error:', e);
    }
}

async function fetchChatHistory() {
    try {
        const res = await fetch('/api/agent/chat/history?limit=25');
        const data = await res.json();
        const history = data.history || [];
        const container = document.getElementById('chatMessages');

        if (history.length > 0) {
            container.innerHTML = history.map(msg => `
                <div class="chat-bubble ${msg.role === 'user' ? 'user' : 'agent'}">
                    ${escapeHtml(msg.message)}
                </div>
            `).join('');
            container.scrollTop = container.scrollHeight;
        }
    } catch (e) {
        console.error('Chat history fetch error:', e);
    }
}

async function handleChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    const container = document.getElementById('chatMessages');

    // Append user message immediately
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = msg;
    container.appendChild(userBubble);

    // Typing placeholder
    const typingBubble = document.createElement('div');
    typingBubble.className = 'chat-bubble agent';
    typingBubble.id = 'agentTypingBubble';
    typingBubble.innerHTML = '<em>Thinking & analyzing strategy... 🧠</em>';
    container.appendChild(typingBubble);
    container.scrollTop = container.scrollHeight;

    try {
        const res = await fetch('/api/agent/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        typingBubble.innerHTML = escapeHtml(data.reply || 'Task processed.');
        container.scrollTop = container.scrollHeight;

        // Refresh stats & queue in case agent triggered an action
        fetchStats();
        fetchQueue(currentTab);
        fetchDecisions();
    } catch (err) {
        typingBubble.textContent = 'Sorry, could not process instruction.';
    }
}

function sendQuickPrompt(promptText) {
    document.getElementById('chatInput').value = promptText;
    document.querySelector('.chat-input-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
}

async function triggerCommentEngagement() {
    showToast('AI engaging audience: liking comments and posting witty replies... 💬');
    try {
        const res = await fetch('/api/instagram/engage', { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
    } catch (e) {
        showToast('Error triggering comment engagement', 'error');
    }
}

async function triggerAgentCycle() {
    showToast('Executing AI Executive strategic cycle... 🧠');
    try {
        const res = await fetch('/api/agent/cycle', { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
        setTimeout(() => {
            fetchDecisions();
            fetchLogs();
            fetchQueue(currentTab);
        }, 3000);
    } catch (e) {
        showToast('Error triggering agent cycle', 'error');
    }
}


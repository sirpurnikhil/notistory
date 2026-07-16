document.addEventListener('DOMContentLoaded', () => {
  const notifications = window.NOTIFICATIONS || [];
  const generatedAt = window.GENERATED_AT || new Date().toISOString();
  
  // State
  let state = {
    tab: 'today', // 'today' or 'earlier'
    appFilter: 'all',
    searchQuery: ''
  };

  // DOM Elements
  const appFilterList = document.getElementById('app-filter-list');
  const notificationList = document.getElementById('notification-list');
  const emptyState = document.getElementById('empty-state');
  const searchBox = document.getElementById('search-box');
  const badgeToday = document.getElementById('badge-today');
  const badgeEarlier = document.getElementById('badge-earlier');
  const updatedAtSpan = document.getElementById('updated-at');
  const tabs = document.querySelectorAll('.tab');

  // Format generated time
  try {
    const genDate = new Date(generatedAt);
    updatedAtSpan.textContent = genDate.toLocaleString(undefined, { 
      dateStyle: 'medium', timeStyle: 'short' 
    });
    updatedAtSpan.title = generatedAt;
  } catch (e) {
    updatedAtSpan.textContent = generatedAt;
  }

  // Pre-process Data
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const todayTs = todayStart.getTime() / 1000;

  const processedNotifs = notifications.map(n => {
    return {
      ...n,
      isToday: (n.ts || 0) >= todayTs,
      searchStr: `${n.app} ${n.summary} ${n.body}`.toLowerCase()
    };
  });

  // Calculate App stats
  const appStats = {};
  processedNotifs.forEach(n => {
    const app = n.app || 'Unknown';
    if (!appStats[app]) {
      appStats[app] = { count: 0, icon: n.icon_path, app: app };
    }
    appStats[app].count++;
    // Keep first seen icon path if not already set
    if (!appStats[app].icon && n.icon_path) {
      appStats[app].icon = n.icon_path;
    }
  });

  const appStatsArray = Object.values(appStats).sort((a, b) => b.count - a.count);

  // Helper: Hashed Color
  function getAvatarColor(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const h = Math.abs(hash) % 360;
    return `hsl(${h}, 65%, 45%)`;
  }

  function getInitials(str) {
    return str ? str.charAt(0).toUpperCase() : '?';
  }

  // Global fallback so a failed <img> (e.g. .xpm icons browsers can't render)
  // swaps to a letter-avatar without inline-HTML quoting problems.
  window.__nhAvatar = function (img) {
    img.outerHTML = createAvatarHTML(
      img.getAttribute('data-app') || '',
      img.getAttribute('data-cls') || ''
    );
  };

  function createIconHTML(iconPath, appName, className) {
    if (iconPath) {
      // URL encode path but keep slashes
      const encoded = iconPath.split('/').map(encodeURIComponent).join('/');
      return `<img src="file://${encoded}" class="${className}" alt="${escapeHtml(appName)}" data-app="${escapeHtml(appName)}" data-cls="${escapeHtml(className)}" onerror="window.__nhAvatar(this)">`;
    }
    return createAvatarHTML(appName, className);
  }

  function createAvatarHTML(appName, className) {
    const color = getAvatarColor(appName);
    const initial = getInitials(appName);
    return `<div class="${className}" style="background-color: ${color}">${initial}</div>`;
  }

  function renderSidebar() {
    let html = `
      <li class="app-item ${state.appFilter === 'all' ? 'active' : ''}" data-app="all">
        <div class="app-item-avatar" style="background-color: var(--accent-color)">*</div>
        <span class="app-name">All apps</span>
        <span class="app-count">${processedNotifs.length}</span>
      </li>
    `;
    
    appStatsArray.forEach(stat => {
      html += `
        <li class="app-item ${state.appFilter === stat.app ? 'active' : ''}" data-app="${escapeHtml(stat.app)}">
          ${createIconHTML(stat.icon, stat.app, 'app-item-icon')}
          <span class="app-name" title="${escapeHtml(stat.app)}">${escapeHtml(stat.app)}</span>
          <span class="app-count">${stat.count}</span>
        </li>
      `;
    });
    
    appFilterList.innerHTML = html;
    
    // Bind events
    appFilterList.querySelectorAll('.app-item').forEach(el => {
      el.addEventListener('click', () => {
        state.appFilter = el.getAttribute('data-app');
        renderSidebar(); // re-render to update active state
        renderContent();
      });
    });
  }

  function escapeHtml(unsafe) {
    return (unsafe || '').toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
  }

  function formatTimeRelative(ts) {
    const diff = (Date.now() / 1000) - ts;
    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    return Math.floor(diff / 86400) + 'd ago';
  }

  function formatDateGroup(ts) {
    const date = new Date(ts * 1000);
    const today = new Date();
    today.setHours(0,0,0,0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    date.setHours(0,0,0,0);
    if (date.getTime() === yesterday.getTime()) {
      return "Yesterday";
    }
    return date.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
  }

  function renderContent() {
    // Filter
    const filtered = processedNotifs.filter(n => {
      if (state.appFilter !== 'all' && n.app !== state.appFilter) return false;
      if (state.searchQuery && !n.searchStr.includes(state.searchQuery)) return false;
      return true;
    });

    const todayNotifs = filtered.filter(n => n.isToday);
    const earlierNotifs = filtered.filter(n => !n.isToday);

    // Update badges
    badgeToday.textContent = todayNotifs.length;
    badgeEarlier.textContent = earlierNotifs.length;

    // Switch tab automatically if empty logic (optional, keeping it simple: just render active tab)
    const activeNotifs = state.tab === 'today' ? todayNotifs : earlierNotifs;

    // Render list
    notificationList.innerHTML = '';
    
    if (processedNotifs.length === 0) {
      notificationList.classList.add('hidden');
      emptyState.classList.remove('hidden');
      emptyState.innerHTML = `
        <h3>No notifications yet</h3>
        <p>Waiting for new desktop notifications.</p>
      `;
      return;
    }

    if (activeNotifs.length === 0) {
      notificationList.classList.add('hidden');
      emptyState.classList.remove('hidden');
      if (state.searchQuery || state.appFilter !== 'all') {
        emptyState.innerHTML = `
          <h3>No matches found</h3>
          <p>Try adjusting your search or app filter.</p>
        `;
      } else if (state.tab === 'today') {
        emptyState.innerHTML = `
          <h3>Nothing today</h3>
          <p>You're all caught up for today.</p>
        `;
      } else {
        emptyState.innerHTML = `
          <h3>No earlier notifications</h3>
          <p>Nothing found before today.</p>
        `;
      }
      return;
    }

    notificationList.classList.remove('hidden');
    emptyState.classList.add('hidden');

    let html = '';
    let lastDateGroup = null;

    activeNotifs.forEach(n => {
      // Date Header for Earlier tab
      if (state.tab === 'earlier') {
        const group = formatDateGroup(n.ts);
        if (group !== lastDateGroup) {
          html += `<div class="date-header">${escapeHtml(group)}</div>`;
          lastDateGroup = group;
        }
      }

      const urgencyClass = `urgency-${n.urgency}`;
      const absoluteTime = new Date(n.ts * 1000).toLocaleString();
      const relativeTime = formatTimeRelative(n.ts);

      html += `
        <div class="card ${urgencyClass}">
          <div class="card-icon">
            ${createIconHTML(n.icon_path, n.app, 'app-item-avatar')}
          </div>
          <div class="card-content">
            <div class="card-header">
              <span class="card-app-name">${escapeHtml(n.app)}</span>
              <span class="card-time" title="${escapeHtml(absoluteTime)}">${escapeHtml(relativeTime)}</span>
            </div>
            ${n.summary ? `<div class="card-summary">${escapeHtml(n.summary)}</div>` : ''}
            ${n.body ? `<div class="card-body">${escapeHtml(n.body)}</div>` : ''}
          </div>
        </div>
      `;
    });

    notificationList.innerHTML = html;
  }

  // Event Listeners
  tabs.forEach(tabBtn => {
    tabBtn.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tabBtn.classList.add('active');
      state.tab = tabBtn.getAttribute('data-tab');
      renderContent();
    });
  });

  searchBox.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase();
    renderContent();
  });

  // Init
  // Fallback to earlier if today is empty and earlier is not
  const initialTodayCount = processedNotifs.filter(n => n.isToday).length;
  if (initialTodayCount === 0 && processedNotifs.length > 0) {
    state.tab = 'earlier';
    tabs.forEach(t => t.classList.remove('active'));
    document.querySelector('.tab[data-tab="earlier"]').classList.add('active');
  }

  renderSidebar();
  renderContent();
});

// Backend URL configuration
const BACKEND_URL = "http://127.0.0.1:5000";

// Global state
let currentUser = { id: null, name: null, age: null, metrics: null, region: "GLOBAL" };
let currentSessionId = null;
let chatHistory = [];
let activeAgent = "Elara";
let activeBackgroundAgents = new Set();
let currentTheme = 'light';
let hasShownGreeting = false;
let greetingInFlight = false;
let loginInFlight = false;
let signupInFlight = false;

// Chat history persistence helpers
function getChatStorageKey() {
  const userId = currentUser && currentUser.id ? currentUser.id : 'anon';
  const sessionId = currentSessionId || 'nosession';
  return `aura_chat_${userId}_${sessionId}`;
}

function saveChatHistory() {
  try {
    const key = getChatStorageKey();
    window.sessionStorage.setItem(key, JSON.stringify(chatHistory));
  } catch (e) {
    // ignore storage errors
  }
}

function loadChatHistoryFromStorage() {
  try {
    const key = getChatStorageKey();
    const raw = window.sessionStorage.getItem(key);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        chatHistory = parsed;
      }
    }
  } catch (e) {
    // ignore storage errors
  }
}

function renderChatHistory() {
  const chatLog = document.getElementById('chat-log');
  if (!chatLog) return;
  chatLog.innerHTML = '';
  chatHistory.forEach(({ text, agent }) => {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${agent === 'user' ? 'user-bubble' : 'ai-bubble'}`;
    bubble.textContent = text;
    chatLog.appendChild(bubble);
  });
  chatLog.scrollTop = chatLog.scrollHeight;
}

// Agent configurations
const AGENTS = {
  Kai: { name: "Kai", icon: "fas fa-clipboard-check", type: "Interactive" },
  Elara: { name: "Elara", icon: "fas fa-comments", type: "Interactive" },
  Vero: { name: "Vero", icon: "fas fa-book-medical", type: "Interactive" },
  Aegis: { name: "Aegis", icon: "fas fa-shield-alt", type: "System" },
  Orion: { name: "Orion", icon: "fas fa-chart-line", type: "System" },
};

// DOM elements
const chatContainer = document.getElementById("chat-log") || document.getElementById("chat-container");
const chatInput = document.getElementById("chatInput") || document.getElementById("chat-input");
const sendBtn = document.querySelector("button.btn-primary");
const historyList = document.getElementById("history-list");
const newChatBtn = document.querySelector(".new-chat-btn");
const logoutBtn = document.querySelector("button.btn-outline-danger");
const agentHeader = document.getElementById("agent-header");

// Theme management
function toggleTheme() {
  currentTheme = currentTheme === 'light' ? 'dark' : 'light';
  document.body.setAttribute('data-theme', currentTheme);
  
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    const icon = themeToggle.querySelector('i');
    if (currentTheme === 'dark') {
      icon.className = 'fas fa-sun';
      themeToggle.title = 'Switch to Light Mode';
    } else {
      icon.className = 'fas fa-moon';
      themeToggle.title = 'Switch to Dark Mode';
    }
  }
  
  localStorage.setItem('aura-theme', currentTheme);
}

function initializeTheme() {
  const savedTheme = localStorage.getItem('aura-theme') || 'light';
  currentTheme = savedTheme;
  document.body.setAttribute('data-theme', currentTheme);
  
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    const icon = themeToggle.querySelector('i');
    if (currentTheme === 'dark') {
      icon.className = 'fas fa-sun';
      themeToggle.title = 'Switch to Light Mode';
    } else {
      icon.className = 'fas fa-moon';
      themeToggle.title = 'Switch to Dark Mode';
    }
  }
}

// Screen management
function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(screen => {
    screen.classList.remove('active');
    screen.style.display = 'none';
  });
  
  const targetScreen = document.getElementById(screenId);
  if (targetScreen) {
    targetScreen.classList.add('active');
    targetScreen.style.display = 'flex';
  }
}

// Metrics functionality
function updateMetricsDisplay(metrics) {
  if (!metrics) return;
  
  const anxietyValue = document.getElementById('anxiety-value');
  const depressionValue = document.getElementById('depression-value');
  const stressValue = document.getElementById('stress-value');
  
  const anxietyFill = document.getElementById('anxiety-fill');
  const depressionFill = document.getElementById('depression-fill');
  const stressFill = document.getElementById('stress-fill');
  
  // Update values numeric 0-100
  anxietyValue.textContent = metrics.anxiety || 0;
  depressionValue.textContent = metrics.depression || 0;
  stressValue.textContent = metrics.stress || 0;
  
  // Update progress bars
  anxietyFill.style.width = `${metrics.anxiety || 0}%`;
  anxietyFill.className = 'metric-fill anxiety';
  
  depressionFill.style.width = `${metrics.depression || 0}%`;
  depressionFill.className = 'metric-fill depression';
  
  stressFill.style.width = `${metrics.stress || 0}%`;
  stressFill.className = 'metric-fill stress';
}

async function reloadMetrics() {
  const reloadBtn = document.getElementById('reload-metrics');
  const icon = reloadBtn.querySelector('i');
  
  // Add loading state
  reloadBtn.classList.add('loading');
  icon.className = 'fas fa-sync-alt';
  
  try {
    // Fetch latest metrics from backend
    const response = await fetch(`${BACKEND_URL}/auth/getMetrics?userId=${currentUser.id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.metrics) {
        updateMetricsDisplay(data.metrics);
        // Update current user metrics
        if (currentUser) {
          currentUser.metrics = data.metrics;
        }
      }
    } else {
      console.error('Failed to reload metrics');
    }
  } catch (error) {
    console.error('Error reloading metrics:', error);
  } finally {
    // Remove loading state
    reloadBtn.classList.remove('loading');
    icon.className = 'fas fa-sync-alt';
  }
}

// Authentication
async function login(event) {
  event.preventDefault();
  if (loginInFlight) return;
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value.trim();
  
  if (!email || !password) {
    alert('Please enter both email and password.');
    return;
  }
  
  try {
    loginInFlight = true;
    const form = document.getElementById('login-form');
    const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
    if (submitBtn) submitBtn.disabled = true;
    const res = await fetch(`${BACKEND_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.toLowerCase(), password }),
    });
    
    if (res.ok) {
      const data = await res.json();
      currentUser = data.user;
      showScreen('app-screen');
      initializeApp(data.hasRecentScreening, currentUser.metrics);
    } else {
      const errorData = await res.json();
      alert(errorData.error || 'Login failed. Please check your credentials.');
    }
  } catch (error) {
    console.error('Login error:', error);
    alert('Login failed. Please try again.');
  } finally {
    loginInFlight = false;
    const form = document.getElementById('login-form');
    const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function signup(event) {
  event.preventDefault();
  if (signupInFlight) return;
  const name = document.getElementById('signupName').value.trim();
  const email = document.getElementById('signupEmail').value.trim();
  const password = document.getElementById('signupPassword').value.trim();
  const age = parseInt(document.getElementById('signupAge').value);
  const region = document.getElementById('signupRegion').value;
  
  if (!name || !email || !password || !age || !region) {
    alert('Please fill in all fields.');
    return;
  }
  
  try {
    signupInFlight = true;
    const form = document.getElementById('signup-form');
    const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
    if (submitBtn) submitBtn.disabled = true;
    const res = await fetch(`${BACKEND_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, age, region }),
    });
    
    if (res.ok) {
      alert('Account created successfully! Please login.');
      showScreen('login-screen');
    } else {
      const errorData = await res.json();
      alert(errorData.error || 'Signup failed. Please try again.');
    }
  } catch (error) {
    console.error('Signup error:', error);
    alert('Signup failed. Please try again.');
  } finally {
    signupInFlight = false;
    const form = document.getElementById('signup-form');
    const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
    if (submitBtn) submitBtn.disabled = false;
  }
}

// App initialization
function initializeApp(skipKai = false, metrics = null) {
  if (skipKai) {
    loadChatInterface(true, metrics);
  } else {
    startScreening();
  }
  updateUserInfo();
  loadHistoryList();
  loadMentalHealthTip();
  
  // Initialize metrics display
  if (metrics) {
    updateMetricsDisplay(metrics);
  }
}

// Screening functionality
function startScreening() {
  setActiveAgent('Kai');
  loadInterface(`<div id="screening-interface">
    <div class="screening-header text-center mb-4">
      <h3>Mental Health Check-in</h3>
      <p class="text-muted">Let's understand how you're feeling today</p>
    </div>
    <div class="progress-container mb-4">
      <div class="progress">
        <div class="progress-bar" role="progressbar" style="width: 0%"></div>
      </div>
      <p id="progress-text" class="text-center mt-2">Question 1 of 10</p>
    </div>
    <div class="screening-content">
      <h4 id="question" class="mb-4"></h4>
      <div id="options" class="d-grid gap-3"></div>
    </div>
  </div>`);
  
  if (!isNewSession) {
    loadChatHistoryFromStorage();
    renderChatHistory();
  }
  handleScreeningResponse();
}

async function handleScreeningResponse(answerIndex = null) {
  try {
    const res = await fetch(`${BACKEND_URL}/kai/screening`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId: currentUser.id,
        userAge: currentUser.age,
        answerIndex: answerIndex
      }),
    });
    
    const data = await res.json();
    
    if (data.error === "screening_cooldown") {
      alert(data.message);
      loadChatInterface(true, currentUser.metrics);
      return;
    }
    
    if (data.message) {
      // Screening completed
      alert(data.message);
      currentSessionId = data.sessionId;
      if (data.metrics) {
        updateMetricsDisplay(data.metrics);
        if (currentUser) currentUser.metrics = data.metrics;
      }
      loadChatInterface(true, currentUser.metrics);
    } else {
      // Continue screening
      document.getElementById('question').textContent = data.question;
      document.getElementById('options').innerHTML = data.options.map((option, index) => 
        `<button class="btn btn-outline-primary" onclick="handleScreeningResponse(${index})">${option}</button>`
      ).join('');
      
      const progress = (data.currentQuestion / data.totalQuestions) * 100;
      document.querySelector('.progress-bar').style.width = `${progress}%`;
      document.getElementById('progress-text').textContent = `Question ${data.currentQuestion} of ${data.totalQuestions}`;
    }
  } catch (error) {
    alert('Screening failed. Please try again.');
  }
}

// Agent management
function buildAgentHeader() {
  if (!agentHeader) return;
  
  agentHeader.innerHTML = Object.entries(AGENTS).map(([key, agent]) => `
    <div class="agent ${key === activeAgent ? 'active' : ''}" onclick="setActiveAgent('${key}')">
      <div class="agent-container ${activeBackgroundAgents.has(key) ? 'background-active' : ''}">
        <div class="agent-status-indicator">
          <div class="status-strip ${key === activeAgent ? 'active-strip' : ''} ${activeBackgroundAgents.has(key) ? 'background-strip' : ''}"></div>
        </div>
        <div class="agent-icon">
          <i class="${agent.icon}"></i>
        </div>
        <div class="agent-info">
          <h5>${agent.name}</h5>
          <p>${agent.type}</p>
        </div>
        <div class="progress-bar">
          <div class="progress-fill"></div>
        </div>
      </div>
    </div>
  `).join('');
}

function setActiveAgent(agentName) {
  activeAgent = agentName;
  buildAgentHeader();
}

function setBackgroundAgentActive(agentName, isActive = true) {
  if (isActive) {
    activeBackgroundAgents.add(agentName);
  } else {
    activeBackgroundAgents.delete(agentName);
  }
  updateAgentVisuals();
}

function updateAgentVisuals() {
  buildAgentHeader();
}

// Region detection
function detectUserRegion() {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const hour = new Date().getHours();
  
  if (timezone.includes('America')) return 'US';
  if (timezone.includes('Europe')) return 'EU';
  if (timezone.includes('Asia')) return 'ASIA';
  if (timezone.includes('Australia')) return 'AU';
  
  return 'GLOBAL';
}

// Chat interface
async function loadChatInterface(isNewSession = false, metrics = null) {
  setActiveAgent('Elara');
  
  if (isNewSession) {
    currentSessionId = null;
    chatHistory = [];
    hasShownGreeting = false;
    greetingInFlight = false;
  }
  
  loadInterface(`<div class="chat-container" id="chat-log">
    ${isNewSession ? '<div class="text-center text-muted mb-3">Starting new conversation...</div>' : ''}
  </div>
  <div class="input-area">
    <input type="text" id="chatInput" class="form-control" placeholder="Type your message..." onkeypress="if(event.key==='Enter') sendMessage()">
    <button class="btn btn-primary" onclick="sendMessage()">Send</button>
  </div>`);
  
  if (isNewSession && metrics && !hasShownGreeting && !greetingInFlight) {
    try {
      // Guard against race conditions causing duplicate greetings
      hasShownGreeting = true;
      greetingInFlight = true;
      const res = await fetch(`${BACKEND_URL}/elara/greeting`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: currentUser.id, metrics }),
      });
      
      if (res.ok) {
        const data = await res.json();
        currentSessionId = data.sessionId;
        if (!data.duplicate) {
          addBubble(data.response, 'elara');
        }
        greetingInFlight = false;
      }
    } catch (error) {
      addBubble("Hello! I'm Elara, your AI companion. How are you feeling today?", 'elara');
      greetingInFlight = false;
    }
  }
}

function addBubble(text, agent, record = true) {
  const chatLog = document.getElementById('chat-log');
  if (!chatLog) return;
  
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${agent === 'user' ? 'user-bubble' : 'ai-bubble'}`;
  bubble.textContent = text;
  
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
  
  if (record) {
    chatHistory.push({ text, agent });
    saveChatHistory();
  }
}

async function sendMessage() {
  const chatInput = document.getElementById('chatInput');
  if (!chatInput) return;
  
  const userMessage = chatInput.value.trim();
  if (!userMessage) return;
  
  addBubble(userMessage, 'user');
  chatInput.value = "";
  chatInput.disabled = true;
  
  const sendButton = chatInput.nextElementSibling;
  if (sendButton) sendButton.disabled = true;
  
  setBackgroundAgentActive('Orion', true);
  
  try {
    const res = await fetch(`${BACKEND_URL}/elara/chat`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ 
        userId: currentUser.id, 
        sessionId: currentSessionId, 
        message: userMessage, 
        region: currentUser.region 
      }),
    });
    
    const data = await res.json();
    setActiveAgent(data.agent);
    
    if (data.sessionId) {
      currentSessionId = data.sessionId;
    }
    
    if (data.agent === 'Aegis') {
      setBackgroundAgentActive('Aegis', true);
      setTimeout(() => setBackgroundAgentActive('Aegis', false), 3000);
    }
    
    addBubble(data.response, data.agent.toLowerCase());
    
    if (data.show_resource_button && data.resource_data) {
      addResourceButton(data.resource_data);
    }
    
    if (data.metrics) {
      updateMetricsDisplay(data.metrics);
      if (currentUser) currentUser.metrics = data.metrics;
    }
    
    setTimeout(() => setBackgroundAgentActive('Orion', false), 2000);
    
  } catch (error) {
    addBubble("Sorry, I'm having trouble connecting.", 'ai');
    setBackgroundAgentActive('Orion', false);
  }
  
  chatInput.disabled = false;
  if (sendButton) sendButton.disabled = false;
  chatInput.focus();
}

function addResourceButton(resourceData) {
  const chatLog = document.getElementById('chat-log');
  if (!chatLog) return;
  
  const resourceButton = document.createElement('div');
  resourceButton.className = 'resource-button-container';
  resourceButton.innerHTML = `
    <button class="btn btn-primary resource-btn" onclick="loadVeroInterface(${JSON.stringify(resourceData).replace(/"/g, '&quot;')})">
      <i class="fas fa-book-medical"></i> View Resource
    </button>
  `;
  
  chatLog.appendChild(resourceButton);
  chatLog.scrollTop = chatLog.scrollHeight;
}

// History management
async function loadHistoryList() {
  const list = document.getElementById('history-list');
  if (!list) return;
  
  list.innerHTML = '<li>Loading your wellness journey...</li>';
  
  try {
    const res = await fetch(`${BACKEND_URL}/elara/getHistoryList`, { 
      method: 'POST', 
      headers: {'Content-Type': 'application/json'}, 
      body: JSON.stringify({ userId: currentUser.id }) 
    });
    
    const sessions = await res.json();
    list.innerHTML = '';
    
    sessions.forEach(session => {
      const item = document.createElement('li');
      item.className = 'history-item';
      item.innerHTML = `<i class="fas fa-heart"></i> ${session.date}`;
      item.onclick = () => viewPastSession(session.id);
      list.appendChild(item);
    });
  } catch (error) { 
    list.innerHTML = '<li>Could not load your wellness journey.</li>'; 
  }
}

async function viewPastSession(sessionId) {
  setActiveAgent('Elara');
  loadInterface(`<div class="chat-container" id="chat-log"><div class="d-flex justify-content-between align-items-center mb-2"><button class="btn btn-secondary btn-sm" onclick="returnToChat()">Back to Active Chat</button><span class="text-muted">Loading past conversation...</span></div></div><div class="input-area"><input type="text" class="form-control" placeholder="This is a read-only view." disabled><button class="btn btn-primary" disabled>Send</button></div>`);
  
  try {
    const res = await fetch(`${BACKEND_URL}/elara/getSession`, { 
      method: 'POST', 
      headers: {'Content-Type': 'application/json'}, 
      body: JSON.stringify({ sessionId }) 
    });
    
    const history = await res.json();
    const chatLog = document.getElementById('chat-log');
    
    if (chatLog) {
      chatLog.innerHTML = '';
      history.forEach(msg => {
        if (msg.user && msg.user !== 'SESSION_START') addBubble(msg.user, 'user', false);
        if (msg.ai) addBubble(msg.ai, 'ai', false);
      });
    }
    
    currentSessionId = sessionId;
  } catch(error) { 
    console.error("Could not view session:", error); 
  }
}

// Interface management
function loadInterface(html) {
  const mainContent = document.getElementById('main-content');
  if (mainContent) mainContent.innerHTML = html;
}

// Enhanced Vero resource interface with better formatting
function loadVeroInterface(resource) {
  setActiveAgent('Vero');
  
  const stepsHTML = resource.steps.map(step => `<li class="resource-step">${step}</li>`).join('');
  
  const veroHTML = `
    <div class="resource-container">
      <div class="resource-card">
        <div class="resource-header">
          <h2 class="resource-title">${resource.title}</h2>
          <div class="resource-source">
            <i class="fas fa-info-circle"></i>
            <span>${resource.source}</span>
          </div>
        </div>
        
        <div class="resource-description">
          <p>${resource.description || 'A helpful technique to support your mental health.'}</p>
        </div>
        
        <div class="resource-instructions">
          <h3>Step-by-Step Instructions:</h3>
          <ol class="resource-steps">
            ${stepsHTML}
          </ol>
        </div>
        
        <div class="resource-footer">
          <a href="${resource.source_url}" target="_blank" class="source-link">
            <i class="fas fa-external-link-alt"></i> Learn More
          </a>
          <button class="btn btn-primary" onclick="returnToChat()">
            <i class="fas fa-arrow-left"></i> Back to Chat
          </button>
        </div>
      </div>
    </div>`;
  
  loadInterface(veroHTML);
}

function returnToChat() {
  loadChatInterface(false, currentUser.metrics);
}

async function handleVeroAction(query) {
  try {
    const res = await fetch(`${BACKEND_URL}/vero/getResource`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, userId: currentUser.id, region: currentUser.region }),
    });
    
    if (!res.ok) throw new Error("Network response was not ok");
    
    const data = await res.json();
    loadVeroInterface(data);
  } catch (error) {
    alert("Could not retrieve that resource.");
    console.error("Vero resource fetch error:", error);
  }
}

function startNewSession(metrics = null) {
  if (metrics) {
    loadChatInterface(true, metrics);
  } else {
    loadChatInterface(true, currentUser.metrics);
  }
}

function logout() {
  if (confirm("Are you sure you want to logout and end the session?")) {
    currentUser = { id: null, name: null, age: null, metrics: null, region: "GLOBAL" };
    currentSessionId = null;
    chatHistory = [];
    
    const userName = document.getElementById('user-name');
    const userStatus = document.getElementById('user-status');
    if (userName) userName.textContent = 'Welcome';
    if (userStatus) userStatus.textContent = 'Offline';
    
    showScreen('login-screen');
    const chatLog = document.getElementById('chat-log');
    if (chatLog) chatLog.innerHTML = "";
    const chatInput = document.getElementById('chatInput');
    if (chatInput) chatInput.value = "";
  }
}

function updateUserInfo() {
  const userName = document.getElementById('user-name');
  const userStatus = document.getElementById('user-status');
  
  if (userName) userName.textContent = currentUser.name || 'Welcome';
  if (userStatus) userStatus.textContent = 'Online';
}

async function loadMentalHealthTip() {
  try {
    const res = await fetch(`${BACKEND_URL}/vero/getMentalHealthTip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId: currentUser.id }),
    });
    
    if (res.ok) {
      const data = await res.json();
      const tipElement = document.getElementById('daily-tip');
      if (tipElement) {
        tipElement.textContent = data.tip;
      }
    }
  } catch (error) {
    console.error('Failed to load mental health tip:', error);
  }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  initializeTheme();
  showScreen('login-screen');
  
  // Add event listeners for forms and buttons
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', login);
  }
  
  const signupForm = document.getElementById('signup-form');
  if (signupForm) {
    signupForm.addEventListener('submit', signup);
  }
  
  const newChatBtn = document.getElementById('new-chat-btn');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => startNewSession());
  }
  
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
  }
  
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }
  
  const reloadMetricsBtn = document.getElementById('reload-metrics');
  if (reloadMetricsBtn) {
    reloadMetricsBtn.addEventListener('click', reloadMetrics);
  }
});

// Global function exports
window.login = login;
window.signup = signup;
window.toggleTheme = toggleTheme;
window.showScreen = showScreen;
window.returnToChat = returnToChat;
window.sendMessage = sendMessage;
window.startNewSession = startNewSession;
window.handleVeroAction = handleVeroAction;

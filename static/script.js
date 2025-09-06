// JavaScript for AI Research Agent

// Global variables
let currentSessionId = null;
let searchInProgress = false;

// DOM Elements
const researchForm = document.getElementById('research-form');
const topicInput = document.getElementById('topic');
const searchBtn = document.getElementById('search-btn');
const loadingSection = document.getElementById('loading-section');
const loadingStatus = document.getElementById('loading-status');
const loadingDetails = document.getElementById('loading-details');
const progressBar = document.getElementById('progress-bar');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkAPIStatus();
});

// Event Listeners
function initializeEventListeners() {
    // Form submission
    researchForm.addEventListener('submit', handleFormSubmit);
    
    // Example topic clicks
    document.querySelectorAll('.example-topic').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const topic = this.textContent.trim();
            topicInput.value = topic;
            topicInput.focus();
        });
    });
    
    // Real-time validation
    topicInput.addEventListener('input', validateTopicInput);
    
    // Enter key handling
    topicInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !searchInProgress) {
            e.preventDefault();
            handleFormSubmit(e);
        }
    });
}

// Form submission handler
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (searchInProgress) {
        return;
    }
    
    const topic = topicInput.value.trim();
    
    if (!validateTopic(topic)) {
        showError('Please enter a valid research topic (3-500 characters)');
        return;
    }
    
    await performResearch(topic);
}

// Research execution
async function performResearch(topic) {
    try {
        searchInProgress = true;
        showLoading();
        updateProgress(0, 'Initializing search...');
        
        // Get form options
        const options = getFormOptions();
        
        // Prepare request data
        const requestData = {
            topic: topic,
            ...options
        };
        
        updateProgress(10, 'Sending request...');
        
        // Make API request
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        updateProgress(20, 'Processing response...');
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Research failed');
        }
        
        updateProgress(100, 'Research completed!');
        
        // Store session ID
        currentSessionId = data.session_id;
        
        // Redirect to results page
        setTimeout(() => {
            window.location.href = `/results/${data.session_id}`;
        }, 1000);
        
    } catch (error) {
        console.error('Research failed:', error);
        showError(error.message);
        hideLoading();
    } finally {
        searchInProgress = false;
    }
}

// Get form options
function getFormOptions() {
    return {
        num_sources: parseInt(document.getElementById('num-sources')?.value || '10'),
        citation_style: document.getElementById('citation-style')?.value || 'apa',
        time_filter: document.getElementById('time-filter')?.value || 'year',
        summary_tone: document.getElementById('summary-tone')?.value || 'academic'
    };
}

// Topic validation
function validateTopic(topic) {
    if (!topic || typeof topic !== 'string') {
        return false;
    }
    
    topic = topic.trim();
    
    // Length check
    if (topic.length < 3 || topic.length > 500) {
        return false;
    }
    
    // Basic spam detection
    const spamPatterns = [
        /^(.)\1{10,}/, // Repeated characters
        /https?:\/\//, // URLs
        /[A-Z]{20,}/   // All caps spam
    ];
    
    for (const pattern of spamPatterns) {
        if (pattern.test(topic)) {
            return false;
        }
    }
    
    return true;
}

// Real-time input validation
function validateTopicInput() {
    const topic = topicInput.value.trim();
    const isValid = validateTopic(topic);
    
    // Update UI based on validation
    if (topic.length === 0) {
        resetInputState();
    } else if (isValid) {
        setInputState('valid');
    } else {
        setInputState('invalid');
    }
    
    // Update button state
    searchBtn.disabled = !isValid || searchInProgress;
}

// Input state management
function setInputState(state) {
    topicInput.classList.remove('is-valid', 'is-invalid');
    
    if (state === 'valid') {
        topicInput.classList.add('is-valid');
    } else if (state === 'invalid') {
        topicInput.classList.add('is-invalid');
    }
}

function resetInputState() {
    topicInput.classList.remove('is-valid', 'is-invalid');
}

// Loading state management
function showLoading() {
    loadingSection.style.display = 'block';
    searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Researching...';
    searchBtn.disabled = true;
    
    // Scroll to loading section
    loadingSection.scrollIntoView({ behavior: 'smooth' });
}

function hideLoading() {
    loadingSection.style.display = 'none';
    searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>Start Research';
    searchBtn.disabled = false;
}

// Progress update
function updateProgress(percentage, status, details = null) {
    progressBar.style.width = `${percentage}%`;
    progressBar.setAttribute('aria-valuenow', percentage);
    loadingStatus.textContent = status;
    
    if (details) {
        loadingDetails.textContent = details;
    }
    
    // Simulate intermediate progress updates
    if (percentage < 100) {
        setTimeout(() => {
            const nextPercentage = Math.min(percentage + Math.random() * 20, 90);
            if (progressBar.style.width.replace('%', '') < 90) {
                updateProgress(nextPercentage, status);
            }
        }, 2000 + Math.random() * 2000);
    }
}

// Error handling
function showError(message) {
    // Create error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Error:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert after form
    researchForm.parentNode.insertBefore(alertDiv, researchForm.nextSibling);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 10000);
}

// API status check
async function checkAPIStatus() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('API is healthy');
        } else {
            console.warn('API health check failed:', data);
        }
    } catch (error) {
        console.error('Failed to check API status:', error);
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            return Promise.resolve();
        } catch (err) {
            return Promise.reject(err);
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

// Export functions for use in other scripts
window.AIResearchAgent = {
    validateTopic,
    showError,
    copyToClipboard,
    formatFileSize,
    debounce
};

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden && searchInProgress) {
        // Page is hidden, but search is in progress
        console.log('Page hidden during search - maintaining connection');
    } else if (!document.hidden && searchInProgress) {
        // Page is visible again
        console.log('Page visible again during search');
    }
});

// Handle beforeunload for ongoing searches
window.addEventListener('beforeunload', function(e) {
    if (searchInProgress) {
        const message = 'Research is in progress. Are you sure you want to leave?';
        e.returnValue = message;
        return message;
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to start search
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !searchInProgress) {
        e.preventDefault();
        if (validateTopic(topicInput.value.trim())) {
            handleFormSubmit(e);
        }
    }
    
    // Escape to clear input
    if (e.key === 'Escape' && !searchInProgress) {
        topicInput.value = '';
        topicInput.focus();
        validateTopicInput();
    }
});

// Auto-save topic to localStorage
const debouncedSave = debounce(function(topic) {
    if (topic && topic.length > 3) {
        localStorage.setItem('ai_research_agent_last_topic', topic);
    }
}, 1000);

topicInput.addEventListener('input', function() {
    debouncedSave(this.value.trim());
});

// Restore last topic on page load
document.addEventListener('DOMContentLoaded', function() {
    const lastTopic = localStorage.getItem('ai_research_agent_last_topic');
    if (lastTopic && !topicInput.value.trim()) {
        // Only restore if input is empty
        // topicInput.value = lastTopic;
        // validateTopicInput();
    }
});

// Performance monitoring
let performanceData = {
    searchStartTime: null,
    searchEndTime: null,
    pageLoadTime: window.performance.timing.loadEventEnd - window.performance.timing.navigationStart
};

// Track search performance
function trackSearchStart() {
    performanceData.searchStartTime = performance.now();
}

function trackSearchEnd() {
    performanceData.searchEndTime = performance.now();
    const duration = performanceData.searchEndTime - performanceData.searchStartTime;
    console.log(`Search completed in ${duration}ms`);
    
    // Could send to analytics service
    // analytics.track('search_completed', { duration });
}

// Add performance tracking to research function
const originalPerformResearch = performResearch;
performResearch = async function(topic) {
    trackSearchStart();
    try {
        await originalPerformResearch(topic);
        trackSearchEnd();
    } catch (error) {
        trackSearchEnd();
        throw error;
    }
};
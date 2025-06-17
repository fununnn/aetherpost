// AetherPost Documentation Site JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeCopyButtons();
    initializeNavigation();
    highlightCode();
});

// Tab functionality
function initializeTabs() {
    const tabContainers = document.querySelectorAll('.install-tabs, .example-tabs');
    
    tabContainers.forEach(container => {
        const headers = container.querySelectorAll('.tab-header');
        const panes = container.querySelectorAll('.tab-pane');
        
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const tabName = header.getAttribute('data-tab');
                
                // Remove active class from all headers and panes in this container
                headers.forEach(h => h.classList.remove('active'));
                panes.forEach(p => p.classList.remove('active'));
                
                // Add active class to clicked header and corresponding pane
                header.classList.add('active');
                const targetPane = container.querySelector(`#${tabName}`);
                if (targetPane) {
                    targetPane.classList.add('active');
                }
            });
        });
    });
}

// Copy to clipboard functionality
function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const codeBlock = button.parentElement;
            const code = codeBlock.querySelector('code');
            if (code) {
                copyToClipboard(code.textContent);
                showCopyNotification();
            }
        });
    });
}

// Copy specific code blocks
function copyCode(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        copyToClipboard(element.textContent);
        showCopyNotification();
    }
}

// Copy install command
function copyInstallCommand() {
    const installCommand = `# Install AetherPost
pip install aetherpost

# Quick setup
aetherpost init main --quick`;
    
    copyToClipboard(installCommand);
    showCopyNotification('Installation commands copied!');
}

// Generic copy to clipboard function
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // Use modern clipboard API
        navigator.clipboard.writeText(text).catch(err => {
            console.error('Failed to copy text: ', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        // Fallback for older browsers
        fallbackCopyTextToClipboard(text);
    }
}

// Fallback copy method
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }
    
    document.body.removeChild(textArea);
}

// Show copy notification
function showCopyNotification(message = 'Copied to clipboard!') {
    // Remove existing notification
    const existing = document.querySelector('.copy-notification');
    if (existing) {
        existing.remove();
    }
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = 'copy-notification';
    notification.innerHTML = `
        <i class="fas fa-check"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide notification after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Navigation functionality
function initializeNavigation() {
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerOffset = 80; // Account for fixed navbar
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Navbar scroll effect
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add/remove shadow based on scroll position
        if (scrollTop > 0) {
            navbar.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        } else {
            navbar.style.boxShadow = 'none';
        }
        
        lastScrollTop = scrollTop;
    });
}

// Code highlighting (if Prism.js is available)
function highlightCode() {
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
}

// Intersection Observer for animations
function initializeAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements that should animate in
    const animatedElements = document.querySelectorAll('.feature-card, .community-card, .example-step');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', initializeAnimations);

// Search functionality (for future implementation)
function initializeSearch() {
    const searchInput = document.querySelector('#search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(performSearch, 300));
    }
}

// Debounce function for search
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

// Search implementation (placeholder)
function performSearch(event) {
    const query = event.target.value.toLowerCase();
    // TODO: Implement search functionality
    console.log('Searching for:', query);
}

// Mobile menu toggle (for future mobile navigation)
function toggleMobileMenu() {
    const mobileMenu = document.querySelector('.mobile-menu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('active');
    }
}

// External link handling
document.addEventListener('DOMContentLoaded', function() {
    const externalLinks = document.querySelectorAll('a[href^="http"]');
    
    externalLinks.forEach(link => {
        // Add external link icon
        if (!link.querySelector('.fa-external-link-alt')) {
            link.innerHTML += ' <i class="fas fa-external-link-alt" style="font-size: 0.8em; opacity: 0.7;"></i>';
        }
        
        // Open in new tab
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
});

// Performance optimizations
function optimizeImages() {
    const images = document.querySelectorAll('img');
    
    if ('loading' in HTMLImageElement.prototype) {
        images.forEach(img => {
            img.loading = 'lazy';
        });
    }
}

// Initialize all optimizations
document.addEventListener('DOMContentLoaded', function() {
    optimizeImages();
    
    // Preload critical resources
    const criticalCSS = document.createElement('link');
    criticalCSS.rel = 'preload';
    criticalCSS.href = 'css/style.css';
    criticalCSS.as = 'style';
    document.head.appendChild(criticalCSS);
});

// Error handling for failed resource loads
window.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
        e.target.style.display = 'none';
        console.warn('Failed to load image:', e.target.src);
    }
});

// Analytics integration (placeholder)
function trackEvent(eventName, properties = {}) {
    // TODO: Integrate with analytics service
    console.log('Event tracked:', eventName, properties);
}

// Track important user interactions
document.addEventListener('click', function(e) {
    const target = e.target.closest('a, button');
    if (target) {
        const text = target.textContent.trim();
        const href = target.href;
        
        if (href && (href.includes('github.com') || href.includes('download'))) {
            trackEvent('external_link_click', {
                text: text,
                url: href
            });
        }
        
        if (target.classList.contains('copy-btn') || target.onclick?.toString().includes('copy')) {
            trackEvent('code_copy', {
                section: target.closest('section')?.id || 'unknown'
            });
        }
    }
});

// Feature detection and progressive enhancement
function enhanceForModernBrowsers() {
    // Check for modern CSS features
    if (CSS.supports('backdrop-filter', 'blur(10px)')) {
        document.body.classList.add('supports-backdrop-filter');
    }
    
    // Check for intersection observer
    if ('IntersectionObserver' in window) {
        document.body.classList.add('supports-intersection-observer');
    }
    
    // Check for clipboard API
    if (navigator.clipboard) {
        document.body.classList.add('supports-clipboard-api');
    }
}

// Initialize enhancements
document.addEventListener('DOMContentLoaded', enhanceForModernBrowsers);
// DOM Elements
const searchInput = document.querySelector('.search-bar input');
const teamDropdown = document.getElementById('teamDropdown');
const shopByTeamLink = document.querySelector('.nav-link');
const sizeButtons = document.querySelectorAll('.size-btn');
const thumbnails = document.querySelectorAll('.thumbnail');
const mainImage = document.querySelector('.main-image img');
const addToCartBtn = document.querySelector('.add-to-cart');
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const mainNav = document.querySelector('.main-nav');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeSlider();
});

// Event Listeners
function initializeEventListeners() {
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('focus', function() {
            this.placeholder = '';
        });
        
        searchInput.addEventListener('blur', function() {
            this.placeholder = 'What can we help you find?';
        });
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch(this.value);
            }
        });
    }
    
    // Team dropdown
    if (shopByTeamLink && teamDropdown) {
        shopByTeamLink.addEventListener('mouseenter', function() {
            teamDropdown.style.display = 'block';
        });
        
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.nav-link') && !e.target.closest('.team-dropdown')) {
                teamDropdown.style.display = 'none';
            }
        });
    }
    
    // Size selection
    sizeButtons.forEach(button => {
        button.addEventListener('click', function() {
            sizeButtons.forEach(btn => btn.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
    
    // Product gallery
    thumbnails.forEach((thumbnail, index) => {
        thumbnail.addEventListener('click', function() {
            thumbnails.forEach(thumb => thumb.classList.remove('active'));
            this.classList.add('active');
            
            // Change main image (in real app, would have different images)
            if (mainImage) {
                mainImage.src = this.src.replace('80x80', '600x600');
            }
        });
    });
    
    // Add to cart
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function() {
            const selectedSize = document.querySelector('.size-btn.selected');
            
            if (!selectedSize) {
                alert('Please select a size');
                return;
            }
            
            // Animation
            this.textContent = 'Adding...';
            this.disabled = true;
            
            setTimeout(() => {
                this.textContent = 'Added to Cart ✓';
                setTimeout(() => {
                    this.textContent = 'Add to Cart';
                    this.disabled = false;
                }, 2000);
            }, 1000);
            
            // Update cart count (in real app, would update cart state)
            updateCartCount();
        });
    }
    
    // Mobile menu
    if (mobileMenuToggle && mainNav) {
        mobileMenuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
    
    // Product image navigation
    const prevArrow = document.querySelector('.nav-arrow.prev');
    const nextArrow = document.querySelector('.nav-arrow.next');
    
    if (prevArrow && nextArrow) {
        let currentImageIndex = 0;
        const totalImages = thumbnails.length;
        
        prevArrow.addEventListener('click', function() {
            currentImageIndex = (currentImageIndex - 1 + totalImages) % totalImages;
            updateGalleryImage(currentImageIndex);
        });
        
        nextArrow.addEventListener('click', function() {
            currentImageIndex = (currentImageIndex + 1) % totalImages;
            updateGalleryImage(currentImageIndex);
        });
    }
}

// Helper Functions
function performSearch(query) {
    if (query.trim() === '') return;
    
    // In real app, would perform actual search
    console.log('Searching for:', query);
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
}

function updateCartCount() {
    const cartBtn = document.querySelector('.cart-btn');
    if (cartBtn) {
        // In real app, would get actual cart count
        const currentCount = parseInt(cartBtn.dataset.count || '0');
        const newCount = currentCount + 1;
        
        cartBtn.dataset.count = newCount;
        
        // Add badge if not exists
        let badge = cartBtn.querySelector('.cart-badge');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'cart-badge';
            cartBtn.appendChild(badge);
        }
        badge.textContent = newCount;
    }
}

function updateGalleryImage(index) {
    thumbnails.forEach((thumb, i) => {
        thumb.classList.toggle('active', i === index);
    });
    
    if (mainImage && thumbnails[index]) {
        mainImage.src = thumbnails[index].src.replace('80x80', '600x600');
    }
}

// Slider functionality (for hero banner if needed)
function initializeSlider() {
    const slider = document.querySelector('.hero-slider');
    if (!slider) return;
    
    let currentSlide = 0;
    const slides = slider.querySelectorAll('.slide');
    const totalSlides = slides.length;
    
    if (totalSlides <= 1) return;
    
    // Auto-advance slides
    setInterval(() => {
        currentSlide = (currentSlide + 1) % totalSlides;
        updateSlider();
    }, 5000);
    
    function updateSlider() {
        slides.forEach((slide, index) => {
            slide.style.transform = `translateX(${(index - currentSlide) * 100}%)`;
        });
    }
}

// Lazy Loading for images
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.add('loaded');
            observer.unobserve(img);
        }
    });
});

// Apply lazy loading to product images
document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img);
});

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Add to cart badge styles (injected via JS)
const style = document.createElement('style');
style.textContent = `
    .cart-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #e10600;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
    }
    
    .cart-btn {
        position: relative;
    }
`;
document.head.appendChild(style);
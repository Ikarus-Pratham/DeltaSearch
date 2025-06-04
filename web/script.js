let uploadedImages = [];
let currentImageIndex = 0;

// DOM Elements
const uploadZone = document.getElementById('upload-zone');
const imageUpload = document.getElementById('image-upload');
const uploadContent = document.getElementById('upload-content');
const previewContent = document.getElementById('preview-content');
const previewImage = document.getElementById('preview-image');
const fileName = document.getElementById('file-name');
const changeImageBtn = document.getElementById('change-image');
const searchBtn = document.getElementById('search-btn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const results = document.getElementById('results');
const productInfo = document.getElementById('product-info');
const imageGallery = document.getElementById('image-gallery');
const imageCount = document.getElementById('image-count');
const fullscreenModal = document.getElementById('fullscreen-modal');
const fullscreenImage = document.getElementById('fullscreen-image');
const closeModal = document.getElementById('close-modal');
const currentImageIndexSpan = document.getElementById('current-image-index');

// Initialize Event Listeners
function initializeEventListeners() {
    // Upload Zone Events
    uploadZone.addEventListener('click', () => imageUpload.click());
    changeImageBtn.addEventListener('click', () => imageUpload.click());

    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);

    imageUpload.addEventListener('change', handleImageUpload);

    // Search Button Event
    searchBtn.addEventListener('click', handleSearch);

    // Modal Events
    closeModal.addEventListener('click', closeFullscreen);
    fullscreenModal.addEventListener('click', handleModalClick);

    // Keyboard Events
    document.addEventListener('keydown', handleKeydown);

    // Fullscreen Events
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    // Touch Events for Mobile
    fullscreenModal.addEventListener('touchstart', handleTouchStart);
    fullscreenModal.addEventListener('touchend', handleTouchEnd);
}

// Upload Zone Event Handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadZone.classList.add('dragover');
}

function handleDragLeave() {
    uploadZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

function handleImageUpload(e) {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
}

function handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file.');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        fileName.textContent = file.name;
        uploadContent.classList.add('hidden');
        previewContent.classList.remove('hidden');
        searchBtn.disabled = false;
        hideError();
    };
    reader.readAsDataURL(file);
}

// Search Functionality
async function handleSearch() {
    if (!imageUpload.files[0]) {
        showError('Please select an image to upload.');
        return;
    }

    const file = imageUpload.files[0];
    const reader = new FileReader();
    reader.onload = async (e) => {
        const imageData = e.target.result;
        
        // Show loading state
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        hideError();

        try {
            const result = await eel.reverse_image_search_and_scrape(imageData, 'test')();
            
            if (result.error) {
                showError(result.error);
                return;
            }

            displayResults(result);
        } catch (err) {
            showError('An error occurred: ' + err);
        } finally {
            loading.classList.add('hidden');
        }
    };
    reader.readAsDataURL(file);
}

function displayResults(result) {
    // Display product info
    productInfo.innerHTML = `
        <div class="space-y-4">
            <h3 class="text-xl font-semibold text-black">${result.product_title}</h3>
            ${result.metadata.size ? `<div class="flex items-center"><i class="fas fa-ruler-combined text-primary mr-2"></i><span><strong>Size:</strong> ${result.metadata.size}</span></div>` : ''}
            <div class="flex items-center">
                <i class="fas fa-calendar text-primary mr-2"></i>
                <span><strong>Search Date:</strong> ${new Date().toLocaleDateString()}</span>
            </div>
        </div>
    `;

    // Display images
    uploadedImages = result.saved_images;
    imageGallery.innerHTML = '';
    imageCount.textContent = `${uploadedImages.length} images found`;

    uploadedImages.forEach((imgData, index) => {
        const imageContainer = document.createElement('div');
        imageContainer.className = 'relative group';
        
        imageContainer.innerHTML = `
            <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow">
                <img src="${imgData}" alt="Product Image ${index + 1}" class="image-box w-full h-70 object-cover" data-index="${index}">
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
                    <i class="fas fa-expand text-white text-2xl opacity-0 group-hover:opacity-100 transition-opacity"></i>
                </div>
            </div>
        `;
        
        const img = imageContainer.querySelector('img');
        img.addEventListener('click', () => openFullscreen(index));
        
        imageGallery.appendChild(imageContainer);
    });

    results.classList.remove('hidden');
}

// Fullscreen Functionality
function openFullscreen(index) {
    currentImageIndex = index;
    fullscreenImage.src = uploadedImages[index];
    currentImageIndexSpan.textContent = `Image ${index + 1} of ${uploadedImages.length}`;
    fullscreenModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    // Enter browser fullscreen mode
    if (fullscreenModal.requestFullscreen) {
        fullscreenModal.requestFullscreen();
    } else if (fullscreenModal.webkitRequestFullscreen) {
        fullscreenModal.webkitRequestFullscreen();
    } else if (fullscreenModal.msRequestFullscreen) {
        fullscreenModal.msRequestFullscreen();
    } else if (fullscreenModal.mozRequestFullScreen) {
        fullscreenModal.mozRequestFullScreen();
    }
}

function closeFullscreen() {
    // Exit browser fullscreen mode
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
    }
    
    fullscreenModal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

// Event Handlers
function handleFullscreenChange() {
    if (!document.fullscreenElement && !document.webkitFullscreenElement && 
        !document.mozFullScreenElement && !document.msFullscreenElement) {
        // Exited fullscreen
        fullscreenModal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

function handleKeydown(e) {
    if (!fullscreenModal.classList.contains('hidden')) {
        if (e.key === 'Escape') {
            closeFullscreen();
        } else if (e.key === 'ArrowLeft' && currentImageIndex > 0) {
            openFullscreen(currentImageIndex - 1);
        } else if (e.key === 'ArrowRight' && currentImageIndex < uploadedImages.length - 1) {
            openFullscreen(currentImageIndex + 1);
        }
    }
}

function handleModalClick(e) {
    if (e.target === fullscreenModal) {
        closeFullscreen();
    }
}

// Touch Events for Mobile Navigation
let touchStartX = 0;
let touchEndX = 0;

function handleTouchStart(e) {
    touchStartX = e.changedTouches[0].screenX;
}

function handleTouchEnd(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    
    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0 && currentImageIndex < uploadedImages.length - 1) {
            // Swipe left - next image
            openFullscreen(currentImageIndex + 1);
        } else if (diff < 0 && currentImageIndex > 0) {
            // Swipe right - previous image
            openFullscreen(currentImageIndex - 1);
        }
    }
}

// Utility Functions
function showError(message) {
    errorMessage.textContent = message;
    error.classList.remove('hidden');
}

function hideError() {
    error.classList.add('hidden');
}

// Initialize the application
document.addEventListener('DOMContentLoaded', initializeEventListeners);
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
const deepSearchSlider = document.getElementById('deep-search');
const searchLevelDisplay = document.getElementById('search-level-display');
const saveFolder = document.getElementById('save-folder');
const selectFolderBtn = document.getElementById('select-folder-btn');

// Initialize Event Listeners
function initializeEventListeners() {
    // Upload Zone Events
    uploadZone.addEventListener('click', () => imageUpload.click());
    changeImageBtn.addEventListener('click', () => imageUpload.click());

    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);

    imageUpload.addEventListener('change', handleImageUpload);

    // Deep Search Slider Events
    deepSearchSlider.addEventListener('input', handleSliderChange);
    deepSearchSlider.addEventListener('change', handleSliderChange);

    // Folder Selection Event
    selectFolderBtn.addEventListener('click', handleFolderSelection);

    // Search Button Event
    searchBtn.addEventListener('click', handleSearch);

    // Keyboard Events
    document.addEventListener('keydown', handleKeydown);

    // Initialize slider display
    updateSliderDisplay();
}

// Slider Event Handlers
function handleSliderChange(e) {
    updateSliderDisplay();
}

function updateSliderDisplay() {
    const value = deepSearchSlider.value;
    searchLevelDisplay.textContent = value;
    deepSearchSlider.setAttribute('data-value', value);
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

// Folder Selection Handler
async function handleFolderSelection() {
    try {
        const folderPath = await eel.select_folder()();
        if (folderPath) {
            saveFolder.value = folderPath;
            hideError();
        } else {
            showError('No folder selected.');
        }
    } catch (err) {
        showError('Error selecting folder: ' + err);
    }
}

// Search Functionality
async function handleSearch() {
    if (!imageUpload.files[0]) {
        showError('Please select an image to upload.');
        return;
    }

    const file = imageUpload.files[0];
    const deepSearchLevel = parseInt(deepSearchSlider.value);
    const saveFolderValue = saveFolder.value.trim();
    
    // Validate inputs
    if (isNaN(deepSearchLevel) || deepSearchLevel < 1 || deepSearchLevel > 10) {
        showError('Please select a valid deep search level (1-10).');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = async (e) => {
        const imageData = e.target.result;
        
        // Show loading state with dynamic message based on search level
        updateLoadingMessage(deepSearchLevel);
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        hideError();

        try {
            // Updated function call with deep_search_level parameter
            const result = await eel.reverse_image_search_and_scrape(
                imageData, 
                saveFolderValue,
                deepSearchLevel
            )();
            
            if (result.error) {
                showError(result.error);
                return;
            }

            displayResults(result, deepSearchLevel);
        } catch (err) {
            showError('An error occurred: ' + err);
        } finally {
            loading.classList.add('hidden');
        }
    };
    reader.readAsDataURL(file);
}

function updateLoadingMessage(searchLevel) {
    const loadingElement = loading.querySelector('p:first-of-type');
    const timeElement = loading.querySelector('p:last-of-type');
    
    let message = 'Searching for similar images...';
    let timeMessage = 'This may take a few moments';
    
    if (searchLevel >= 8) {
        message = 'Performing deep analysis...';
        timeMessage = 'This will take several minutes due to comprehensive search';
    } else if (searchLevel >= 6) {
        message = 'Conducting thorough search...';
        timeMessage = 'This may take a few minutes for detailed results';
    } else if (searchLevel >= 4) {
        message = 'Searching with enhanced precision...';
        timeMessage = 'This may take a minute or two';
    }
    
    loadingElement.textContent = message;
    timeElement.textContent = timeMessage;
}

function displayResults(result, searchLevel) {
    const saveFolderValue = saveFolder.value.trim();
    
    // Display search information
    productInfo.innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center">
                <i class="fas fa-calendar text-primary mr-2"></i>
                <span><strong>Search Date:</strong> ${new Date().toLocaleDateString()}</span>
            </div>
            <div class="flex items-center">
                <i class="fas fa-search-plus text-primary mr-2"></i>
                <span><strong>Deep Search Level:</strong> ${searchLevel}/10</span>
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
                <img src="${imgData}" alt="Similar Image ${index + 1}" class="image-box w-full h-70 object-cover" data-index="${index}">
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
                    <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                        <i class="fas fa-search text-white text-2xl"></i>
                    </div>
                </div>
            </div>
        `;
        
        imageGallery.appendChild(imageContainer);
    });

    results.classList.remove('hidden');
}

function getSearchIntensityText(level) {
    const intensityMap = {
        1: 'Quick Scan',
        2: 'Basic Search',
        3: 'Standard Search',
        4: 'Enhanced Search',
        5: 'Detailed Search',
        6: 'Thorough Analysis',
        7: 'Comprehensive Search',
        8: 'Deep Analysis',
        9: 'Intensive Search',
        10: 'Maximum Depth'
    };
    return intensityMap[level] || 'Standard Search';
}

// Keyboard Events
function handleKeydown(e) {
    if (e.key === 'Enter' && !searchBtn.disabled) {
        handleSearch();
    }
    
    // Allow arrow keys to control slider when focused
    if (document.activeElement === deepSearchSlider) {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
            e.preventDefault();
            const newValue = Math.max(1, parseInt(deepSearchSlider.value) - 1);
            deepSearchSlider.value = newValue;
            updateSliderDisplay();
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
            e.preventDefault();
            const newValue = Math.min(10, parseInt(deepSearchSlider.value) + 1);
            deepSearchSlider.value = newValue;
            updateSliderDisplay();
        }
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
    const swipeDistance = touchEndX - touchStartX;
    
    if (Math.abs(swipeDistance) > swipeThreshold) {
        if (swipeDistance > 0) {
            // Swipe right - previous image
            navigateImage(-1);
        } else {
            // Swipe left - next image
            navigateImage(1);
        }
    }
}

function navigateImage(direction) {
    if (uploadedImages.length === 0) return;
    
    currentImageIndex = (currentImageIndex + direction + uploadedImages.length) % uploadedImages.length;
    // Update current image display if needed
}

// Utility Functions
function showError(message) {
    errorMessage.textContent = message;
    error.classList.remove('hidden');
    // Auto-hide error after 5 seconds
    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    error.classList.add('hidden');
}

// Advanced slider interaction
function initializeSliderInteractions() {
    // Add click-to-set functionality
    deepSearchSlider.addEventListener('click', (e) => {
        const rect = deepSearchSlider.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        const newValue = Math.round(percentage * 9) + 1; // 1-10 range
        deepSearchSlider.value = Math.max(1, Math.min(10, newValue));
        updateSliderDisplay();
    });
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeSliderInteractions();
});
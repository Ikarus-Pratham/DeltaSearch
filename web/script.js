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
const numResults = document.getElementById('num-results');
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

    // Folder Selection Event
    selectFolderBtn.addEventListener('click', handleFolderSelection);

    // Search Button Event
    searchBtn.addEventListener('click', handleSearch);

    // Keyboard Events
    document.addEventListener('keydown', handleKeydown);
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
    const numResultsValue = parseInt(numResults.value);
    const saveFolderValue = saveFolder.value.trim();
    
    // Validate inputs
    if (isNaN(numResultsValue) || numResultsValue < 1 || numResultsValue > 100) {
        showError('Please enter a valid number of results (1-100).');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = async (e) => {
        const imageData = e.target.result;
        
        // Show loading state
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        hideError();

        try {
            // Updated function call with num_results and save_folder parameters
            const result = await eel.reverse_image_search_and_scrape(
                imageData, 
                saveFolderValue,
                numResultsValue
            )();
            
            if (result.error) {
                showError(result.error);
                return;
            }

            displayResults(result, numResultsValue);
        } catch (err) {
            showError('An error occurred: ' + err);
        } finally {
            loading.classList.add('hidden');
        }
    };
    reader.readAsDataURL(file);
}

function displayResults(result, requestedResults) {
    const saveFolderValue = saveFolder.value.trim();
    // Display product info
    productInfo.innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center">
                <i class="fas fa-calendar text-primary mr-2"></i>
                <span><strong>Search Date:</strong> ${new Date().toLocaleDateString()}</span>
            </div>
            <div class="flex items-center">
                <i class="fas fa-list-ol text-primary mr-2"></i>
                <span><strong>Requested Results:</strong> ${requestedResults}</span>
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
                    <i class="text-white text-2xl opacity-0 transition-opacity"></i>
                </div>
            </div>
        `;
        
        imageGallery.appendChild(imageContainer);
    });

    results.classList.remove('hidden');
}

// Keyboard Events
function handleKeydown(e) {
    if (e.key === 'Enter' && !searchBtn.disabled) {
        handleSearch();
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
}

function hideError() {
    error.classList.add('hidden');
}

// Initialize the application
document.addEventListener('DOMContentLoaded', initializeEventListeners);
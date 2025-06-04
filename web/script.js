document.getElementById('search-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('image-upload');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const productInfoDiv = document.getElementById('product-info');
    const imageGalleryDiv = document.getElementById('image-gallery');

    if (!fileInput.files[0]) {
        errorDiv.textContent = 'Please select an image to upload.';
        errorDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = async (e) => {
        const imageData = e.target.result;
        resultsDiv.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        productInfoDiv.innerHTML = '<p>Loading...</p>';
        imageGalleryDiv.innerHTML = '';

        try {
            const result = await eel.reverse_image_search_and_scrape(imageData, 'test')();
            if (result.error) {
                errorDiv.textContent = result.error;
                errorDiv.classList.remove('hidden');
                productInfoDiv.innerHTML = '';
                return;
            }

            // Display product info
            productInfoDiv.innerHTML = `
                <h3 class="text-xl font-semibold">${result.product_title}</h3>
                <p><strong>Source:</strong> ${result.source}</p>
                <p><a href="${result.product_url}" target="_blank" class="text-blue-500 underline">View Product</a></p>
                ${result.metadata.size ? `<p><strong>Size:</strong> ${result.metadata.size}</p>` : ''}
                ${result.metadata.source_name ? `<p><strong>Source Name:</strong> ${result.metadata.source_name}</p>` : ''}
            `;

            // Display images
            result.saved_images.forEach((imgData, index) => {
                const imgElement = document.createElement('img');
                imgElement.src = imgData;
                imgElement.alt = `Product Image ${index + 1}`;
                imageGalleryDiv.appendChild(imgElement);
            });
        } catch (err) {
            errorDiv.textContent = 'An error occurred: ' + err;
            errorDiv.classList.remove('hidden');
            productInfoDiv.innerHTML = '';
        }
    };
    reader.readAsDataURL(file);
});
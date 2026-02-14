document.addEventListener('DOMContentLoaded', function() {
    const productTypeField = document.querySelector('#id_product_type');
    const cakeFields = document.querySelectorAll('.cake-field').closest('.form-row');
    
    function toggleCakeFields() {
        const isCake = productTypeField.value === 'cake';
        cakeFields.forEach(field => {
            field.style.display = isCake ? '' : 'none';
        });
    }
    
    if (productTypeField) {
        productTypeField.addEventListener('change', toggleCakeFields);
        toggleCakeFields(); // Initial toggle
    }
});

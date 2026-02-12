// Question list - auto-submit filter form

const filterForm = document.getElementById('filterForm');
if (filterForm) {
    const subjectSelect = document.getElementById('subject');
    const includeSubCheckbox = document.getElementById('include_sub');
    
    if (subjectSelect) {
        subjectSelect.addEventListener('change', function() {
            filterForm.submit();
        });
    }
    
    if (includeSubCheckbox) {
        includeSubCheckbox.addEventListener('change', function() {
            filterForm.submit();
        });
    }

    const stateSelect = document.getElementById('state');
    if (stateSelect) {
        stateSelect.addEventListener('change', function() {
            filterForm.submit();
        });
    }
}

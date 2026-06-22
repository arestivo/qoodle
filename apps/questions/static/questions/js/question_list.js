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

const toggleQuestionTextBtn = document.getElementById('toggleQuestionTextBtn');
if (toggleQuestionTextBtn) {
    const questionTextRows = document.querySelectorAll('.question-text-row');
    const icon = toggleQuestionTextBtn.querySelector('i');
    const label = toggleQuestionTextBtn.querySelector('span');

    toggleQuestionTextBtn.addEventListener('click', function() {
        const shouldShow = toggleQuestionTextBtn.getAttribute('aria-expanded') !== 'true';

        questionTextRows.forEach(function(row) {
            row.classList.toggle('d-none', !shouldShow);
        });

        toggleQuestionTextBtn.setAttribute('aria-expanded', String(shouldShow));
        icon.classList.toggle('fa-eye', !shouldShow);
        icon.classList.toggle('fa-eye-slash', shouldShow);
        label.textContent = shouldShow ? 'Hide Questions' : 'Show Questions';
    });
}
